import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd


def normalize_text_content(
    text: str,
    strip_html: bool = True,
    normalize_unicode: bool = True,
    strip_extra_whitespace: bool = True,
    case_mode: Optional[str] = None  # "lower", "upper", "title", None
) -> str:
    """
    Step 16: Cleans and standardizes individual text strings.
    Strips HTML markup, normalizes Unicode characters, trims irregular whitespace,
    and handles casing.
    """
    if not isinstance(text, str):
        return "" if text is None else str(text)

    s = text

    # Unicode normalization (NFKC decomposes compatibility chars and recomposes canonically)
    if normalize_unicode:
        s = unicodedata.normalize('NFKC', s)

    # Strip HTML tags
    if strip_html:
        s = re.sub(r'<[^>]*?>', '', s)

    # Clean whitespace
    if strip_extra_whitespace:
        s = re.sub(r'[\r\n\t]+', ' ', s)
        s = re.sub(r'\s{2,}', ' ', s)
        s = s.strip()

    # Case normalization
    if case_mode == "lower":
        s = s.lower()
    elif case_mode == "upper":
        s = s.upper()
    elif case_mode == "title":
        s = s.title()

    return s


def clean_text_dataframe(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    strip_html: bool = True,
    normalize_unicode: bool = True,
    strip_whitespace: bool = True,
    case_mode: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Step 16: Applies text normalization across all text/string columns in a DataFrame.
    """
    df_clean = df.copy()
    cleaned_columns = []
    
    target_cols = columns or [c for c in df_clean.columns if df_clean[c].dtype == 'object']
    
    for col in target_cols:
        if col not in df_clean.columns:
            continue
            
        non_null_mask = df_clean[col].notna()
        df_clean.loc[non_null_mask, col] = df_clean.loc[non_null_mask, col].astype(str).apply(
            lambda x: normalize_text_content(
                x,
                strip_html=strip_html,
                normalize_unicode=normalize_unicode,
                strip_extra_whitespace=strip_whitespace,
                case_mode=case_mode
            )
        )
        cleaned_columns.append(col)

    return df_clean, {
        "text_columns_cleaned": cleaned_columns,
        "strip_html": strip_html,
        "normalize_unicode": normalize_unicode,
        "strip_whitespace": strip_whitespace,
        "case_mode": case_mode
    }
