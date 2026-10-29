import re
import uuid
from typing import List, Dict, Any, Optional
from app.services.rag.document_parser import ParsedSection


class ChunkResult:
    def __init__(
        self,
        chunk_index: int,
        chunk_text: str,
        token_count: int,
        page_number: Optional[int],
        section_title: Optional[str],
        metadata: Dict[str, Any]
    ):
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text
        self.token_count = token_count
        self.page_number = page_number
        self.section_title = section_title
        self.metadata = metadata


def estimate_token_count(text: str) -> int:
    """
    Approximates token count based on whitespace and punctuation splits (~4 characters per token).
    """
    if not text:
        return 0
    return max(1, len(text.strip().split()))


def recursive_split_text(
    text: str,
    max_chunk_size: int = 800,
    overlap: int = 150
) -> List[str]:
    """
    Recursively splits text into coherent chunks respecting paragraph, newline,
    sentence, and whitespace boundaries.
    """
    text = text.strip()
    if len(text) <= max_chunk_size:
        return [text] if text else []

    # Delimiter hierarchy
    delimiters = ["\n\n", "\n", ". ", "; ", ", ", " "]
    chunks: List[str] = []
    
    # Try the largest delimiter that appears in the text
    chosen_delim = None
    for d in delimiters:
        if d in text:
            chosen_delim = d
            break

    if not chosen_delim:
        # Fallback to hard character boundary
        for i in range(0, len(text), max_chunk_size - overlap):
            c = text[i:i + max_chunk_size].strip()
            if c:
                chunks.append(c)
        return chunks

    parts = text.split(chosen_delim)
    current_chunk: List[str] = []
    current_length = 0

    for part in parts:
        part_str = part.strip()
        if not part_str:
            continue

        # If a single part exceeds max_chunk_size, flush current and recursively sub-split
        if len(part_str) > max_chunk_size:
            if current_chunk:
                assembled = chosen_delim.join(current_chunk).strip()
                if assembled:
                    chunks.append(assembled)
                current_chunk = []
                current_length = 0

            sub_chunks = recursive_split_text(part_str, max_chunk_size=max_chunk_size, overlap=overlap)
            chunks.extend(sub_chunks)
            continue
            
        part_len = len(part_str) + len(chosen_delim)

        if current_length + part_len > max_chunk_size and current_chunk:
            assembled = chosen_delim.join(current_chunk).strip()
            if assembled:
                chunks.append(assembled)
            
            # Preserve overlap from tail of current_chunk
            overlap_parts = []
            overlap_len = 0
            for prev_part in reversed(current_chunk):
                if overlap_len + len(prev_part) <= overlap:
                    overlap_parts.insert(0, prev_part)
                    overlap_len += len(prev_part)
                else:
                    break
            
            current_chunk = overlap_parts + [part_str]
            current_length = sum(len(p) + len(chosen_delim) for p in current_chunk)
        else:
            current_chunk.append(part_str)
            current_length += part_len

    if current_chunk:
        assembled = chosen_delim.join(current_chunk).strip()
        if assembled:
            chunks.append(assembled)

    return chunks


def chunk_document_sections(
    sections: List[ParsedSection],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    doc_metadata: Optional[Dict[str, Any]] = None
) -> List[ChunkResult]:
    """
    Transforms extracted parsed sections into indexed semantic chunks,
    preserving heading context, page provenance, and token estimations.
    """
    results: List[ChunkResult] = []
    chunk_idx = 0
    seen_hashes = set()
    base_meta = doc_metadata or {}

    for section in sections:
        if not section.text:
            continue

        raw_chunks = recursive_split_text(section.text, max_chunk_size=chunk_size, overlap=chunk_overlap)
        for rc in raw_chunks:
            cleaned = rc.strip()
            if len(cleaned) < 20:  # Ignore trivial or empty fragments
                continue

            # Deduplication of identical contiguous fragments
            chunk_hash = hash(cleaned)
            if chunk_hash in seen_hashes:
                continue
            seen_hashes.add(chunk_hash)

            tokens = estimate_token_count(cleaned)
            meta = {
                **base_meta,
                "section_title": section.section_title,
                "page_number": section.page_number,
                "character_count": len(cleaned)
            }

            results.append(ChunkResult(
                chunk_index=chunk_idx,
                chunk_text=cleaned,
                token_count=tokens,
                page_number=section.page_number,
                section_title=section.section_title,
                metadata=meta
            ))
            chunk_idx += 1

    return results

