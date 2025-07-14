# utils/pdfManager.py
import io
import os
from pathlib import Path
from typing import Union, BinaryIO

from pypdf import PdfReader   # or `from PyPDF2 import PdfReader` if you use PyPDF2


def read_pdf(source: Union[str, os.PathLike, bytes, BinaryIO]) -> str:
    """
    Extract all text from a PDF.

    Parameters
    ----------
    source
        • Path-like (str | Path) – points to a PDF on disk  
        • bytes – raw PDF bytes  
        • file-like object – any object with .read() (e.g., io.BytesIO,
          botocore.response.StreamingBody, tempfile._TemporaryFileWrapper…)

    Returns
    -------
    str
        Concatenated text of every page (empty string for pages without text).

    Raises
    ------
    RuntimeError
        If the file is encrypted and cannot be decrypted with an empty password.
    """
    # --- Normalise the input into a readable binary stream ------------------
    close_after = False  # to know if we opened something that we must close

    if isinstance(source, (str, os.PathLike, Path)):
        stream = open(os.fspath(source), "rb")
        close_after = True

    elif isinstance(source, bytes):
        stream = io.BytesIO(source)

    else:  # already a file-like object (StreamingBody, BytesIO, etc.)
        stream = source
        # make sure we start at the beginning
        if hasattr(stream, "seek"):
            try:
                stream.seek(0)
            except Exception:
                pass

    # --- Read the PDF -------------------------------------------------------
    try:
        reader = PdfReader(stream)

        if reader.is_encrypted:
            try:
                reader.decrypt("")  # empty password
            except Exception as err:
                raise RuntimeError(f"Failed to decrypt PDF: {err}") from err

        return "".join(page.extract_text() or "" for page in reader.pages)

    finally:
        if close_after:
            stream.close()

def separate_pdf_pages(pdf_file: str) -> list[str]:
    """
    Separate a PDF file into individual pages.

    Parameters
    ----------
    pdf_file : str
        Path to the PDF file.

    Returns
    -------
    list[str]
        List of strings, each representing the text of a single page.
    """
    pdf_reader = PdfReader(pdf_file)
    return [page.extract_text() or "" for page in pdf_reader.pages]