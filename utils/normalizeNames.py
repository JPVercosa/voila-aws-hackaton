from pathlib import Path

def normalize_basename(filename: str) -> str:
    """Always strip path and extension."""
    return Path(filename).stem

def make_pdf_name(basename: str) -> str:
    return f"{normalize_basename(basename)}.pdf"

def make_md_name(basename: str) -> str:
    return f"{normalize_basename(basename)}.md"

def make_sections_name(basename: str, method: str) -> str:
    return f"{method}_{normalize_basename(basename)}.json"