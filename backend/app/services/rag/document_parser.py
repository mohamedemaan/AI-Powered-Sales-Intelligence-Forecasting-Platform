import os
import re
import csv
import json
import io
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple


class ParsedSection:
    def __init__(self, text: str, page_number: Optional[int] = None, section_title: Optional[str] = None):
        self.text = text.strip()
        self.page_number = page_number
        self.section_title = section_title or "General"


def parse_pdf_document(file_path: str) -> List[ParsedSection]:
    """
    Extracts text from a PDF document, preserving page numbers.
    Uses pypdf if installed; otherwise utilizes native zero-dependency
    PDF stream and text-operator extractor. Explicitly detects scanned
    PDFs with 0 extracted text characters.
    """
    sections: List[ParsedSection] = []

    # Attempt pypdf first if available
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        if reader.is_encrypted:
            raise ValueError("Encrypted or password-protected PDF files are not supported.")

        for idx, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text() or ""
            extracted = extracted.strip()
            if extracted:
                sections.append(ParsedSection(
                    text=extracted,
                    page_number=idx,
                    section_title=f"Page {idx}"
                ))

        if sections:
            return sections
    except Exception as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            raise ValueError("Encrypted or password-protected PDF files cannot be processed.")

    # Native zero-dependency stream parser fallback
    try:
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        if not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF header signature.")

        # Split into probable page blocks via /Type /Page
        page_chunks = re.split(rb"/Type\s*/Page\b", pdf_bytes)
        if len(page_chunks) > 1:
            for p_idx, chunk in enumerate(page_chunks[1:], start=1):
                # Find all text between parenthesis inside BT ... ET blocks or string literals
                text_matches = re.findall(rb"\((.*?)\)\s*T[jJ]", chunk)
                page_text_parts = []
                for m in text_matches:
                    try:
                        clean_part = m.decode("latin1", errors="ignore").strip()
                        if clean_part:
                            page_text_parts.append(clean_part)
                    except Exception:
                        pass
                
                page_str = " ".join(page_text_parts)
                # Normalize whitespace
                page_str = re.sub(r"\s+", " ", page_str).strip()
                if page_str:
                    sections.append(ParsedSection(
                        text=page_str,
                        page_number=p_idx,
                        section_title=f"Page {p_idx}"
                    ))
        else:
            # Fallback: find all text operators across stream
            text_matches = re.findall(rb"\((.*?)\)\s*T[jJ]", pdf_bytes)
            all_text = " ".join([m.decode("latin1", errors="ignore") for m in text_matches])
            all_text = re.sub(r"\s+", " ", all_text).strip()
            if all_text:
                sections.append(ParsedSection(text=all_text, page_number=1, section_title="Document Content"))

    except Exception as e:
        raise ValueError(f"Could not parse PDF content: {str(e)}")

    if not sections:
        raise ValueError("Scanned or image-only PDF detected. No extractable text found (OCR required).")

    return sections


def parse_docx_document(file_path: str) -> List[ParsedSection]:
    """
    Extracts text from a DOCX file using native zipfile and xml parsing.
    Preserves heading paragraphs and section titles without external dependencies.
    """
    sections: List[ParsedSection] = []
    try:
        with zipfile.ZipFile(file_path, "r") as docx_zip:
            if "word/document.xml" not in docx_zip.namelist():
                raise ValueError("Corrupt DOCX archive: word/document.xml not found.")

            xml_content = docx_zip.read("word/document.xml")
            tree = ET.fromstring(xml_content)

            ns = {
                "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            }

            current_section_title = "Overview"
            current_paragraphs: List[str] = []
            page_counter = 1

            for p in tree.iter(f"{{{ns['w']}}}p"):
                # Check for heading style
                p_style = p.find(f".//{{{ns['w']}}}pStyle")
                style_val = p_style.attrib.get(f"{{{ns['w']}}}val", "") if p_style is not None else ""

                # Extract all text in paragraph
                texts = [node.text for node in p.iter(f"{{{ns['w']}}}t") if node.text]
                p_text = "".join(texts).strip()

                if not p_text:
                    continue

                if "heading" in style_val.lower() or style_val.startswith("Heading"):
                    if current_paragraphs:
                        sections.append(ParsedSection(
                            text="\n\n".join(current_paragraphs),
                            page_number=page_counter,
                            section_title=current_section_title
                        ))
                        current_paragraphs = []
                    current_section_title = p_text
                else:
                    current_paragraphs.append(p_text)

            if current_paragraphs:
                sections.append(ParsedSection(
                    text="\n\n".join(current_paragraphs),
                    page_number=page_counter,
                    section_title=current_section_title
                ))

    except zipfile.BadZipFile:
        raise ValueError("Invalid or corrupted DOCX file.")
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX document: {str(e)}")

    if not sections:
        raise ValueError("DOCX document contains no readable text.")

    return sections


def parse_text_markdown_document(file_path: str) -> List[ParsedSection]:
    """
    Parses plain text (.txt) and markdown (.md) documents.
    Detects Markdown headings (# Header) to construct structured sections.
    """
    sections: List[ParsedSection] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        lines = content.splitlines()
        current_title = "Document Overview"
        current_lines: List[str] = []
        page_approx = 1
        line_count = 0

        for line in lines:
            line_count += 1
            if line_count > 60:
                page_approx += 1
                line_count = 0

            # Markdown header detection
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if header_match:
                if current_lines:
                    text_block = "\n".join(current_lines).strip()
                    if text_block:
                        sections.append(ParsedSection(
                            text=text_block,
                            page_number=page_approx,
                            section_title=current_title
                        ))
                    current_lines = []
                current_title = header_match.group(2).strip()
            else:
                current_lines.append(line)

        if current_lines:
            text_block = "\n".join(current_lines).strip()
            if text_block:
                sections.append(ParsedSection(
                    text=text_block,
                    page_number=page_approx,
                    section_title=current_title
                ))

    except Exception as e:
        raise ValueError(f"Failed to read text document: {str(e)}")

    if not sections:
        raise ValueError("Text document is empty or contains no extractable content.")

    return sections


def parse_csv_tsv_document(file_path: str, delimiter: str = ",") -> List[ParsedSection]:
    """
    Parses tabular CSV or TSV files into rich, contextual text blocks.
    Preserves column names and generates human-readable record summaries.
    """
    sections: List[ParsedSection] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)

        if not rows or len(rows) < 2:
            raise ValueError("Tabular file must contain a header row and at least one data record.")

        header = [col.strip() for col in rows[0]]
        total_rows = len(rows) - 1

        # Summary section
        summary_text = (
            f"Tabular Dataset: {os.path.basename(file_path)}\n"
            f"Columns: {', '.join(header)}\n"
            f"Total Ingested Rows: {total_rows}\n"
        )
        sections.append(ParsedSection(text=summary_text, page_number=1, section_title="Dataset Schema Summary"))

        # Batch rows into semantic chunk blocks of 10 rows
        batch_size = 10
        for i in range(1, len(rows), batch_size):
            chunk_rows = rows[i:i + batch_size]
            row_texts = []
            for r_idx, r in enumerate(chunk_rows, start=i):
                row_dict = {header[c_idx]: r[c_idx] for c_idx in range(min(len(header), len(r)))}
                row_str = f"Record #{r_idx}: " + "; ".join(f"{k}={v}" for k, v in row_dict.items() if v)
                row_texts.append(row_str)

            sections.append(ParsedSection(
                text="\n".join(row_texts),
                page_number=(i // 40) + 1,
                section_title=f"Records {i} to {min(i + batch_size - 1, total_rows)}"
            ))

    except Exception as e:
        raise ValueError(f"Failed to parse tabular data: {str(e)}")

    return sections


def parse_json_document(file_path: str) -> List[ParsedSection]:
    """
    Parses structured JSON documents, converting hierarchical schemas or entity lists
    into coherent contextual sections.
    """
    sections: List[ParsedSection] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        if isinstance(data, list):
            # Array of items / records
            sections.append(ParsedSection(
                text=f"JSON Entity Collection: Total {len(data)} objects.",
                page_number=1,
                section_title="JSON Overview"
            ))
            batch_size = 8
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                text_block = "\n---\n".join(json.dumps(item, indent=2) for item in batch)
                sections.append(ParsedSection(
                    text=text_block,
                    page_number=(i // 25) + 1,
                    section_title=f"Entities {i + 1} to {min(i + batch_size, len(data))}"
                ))
        elif isinstance(data, dict):
            # Key-value or hierarchical object
            sections.append(ParsedSection(
                text=f"Structured JSON Schema: Keys [{', '.join(data.keys())}]",
                page_number=1,
                section_title="Root Schema"
            ))
            for k, v in data.items():
                val_str = json.dumps(v, indent=2) if isinstance(v, (dict, list)) else str(v)
                sections.append(ParsedSection(
                    text=f"Section '{k}':\n{val_str}",
                    page_number=1,
                    section_title=f"Key: {k}"
                ))
        else:
            sections.append(ParsedSection(text=str(data), page_number=1, section_title="Raw JSON Value"))

    except Exception as e:
        raise ValueError(f"Failed to parse JSON document: {str(e)}")

    if not sections:
        raise ValueError("JSON document contains no parsable data.")

    return sections


def extract_document_sections(file_path: str, file_type: str) -> List[ParsedSection]:
    """
    Universal dispatcher for document text extraction based on verified file format.
    """
    ft = file_type.lower().strip()
    if ft == "pdf":
        return parse_pdf_document(file_path)
    elif ft in ["docx", "doc"]:
        return parse_docx_document(file_path)
    elif ft in ["txt", "md", "markdown", "text"]:
        return parse_text_markdown_document(file_path)
    elif ft == "csv":
        return parse_csv_tsv_document(file_path, delimiter=",")
    elif ft == "tsv":
        return parse_csv_tsv_document(file_path, delimiter="\t")
    elif ft in ["json", "jsonl"]:
        return parse_json_document(file_path)
    else:
        raise ValueError(f"Unsupported file format '{file_type}'. Supported formats: PDF, DOCX, TXT, MD, CSV, TSV, JSON.")

