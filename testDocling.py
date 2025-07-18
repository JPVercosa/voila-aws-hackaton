import os
from io import BytesIO
from docling.document_converter import DocumentConverter, DocumentStream

os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

def convert_pdf_to_markdown(file_path: str) -> str:
    """
    Convert a PDF file to Markdown format using Docling.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Path to the converted Markdown file.
    """
    # try:
    with open(file_path, "rb") as f:
        source_stream = DocumentStream(name=file_path, stream=BytesIO(f.read()))
    converter = DocumentConverter()
    result = converter.convert(source_stream).document
    markdown = result.export_to_markdown()
    
    md_file_path = file_path.rsplit(".", 1)[0] + ".md"
    with open(md_file_path, "w", encoding="utf-8") as md_file:
        md_file.write(markdown)
    
    return md_file_path
# except Exception as e:
    #     raise RuntimeError(f"Error converting PDF to Markdown: {e}")
    
if __name__ == "__main__":
    # Example usage
    pdf_file_path = os.path.join("tmp", "Politica_Ambiental_2024.pdf")
    try:
        md_file_path = convert_pdf_to_markdown(pdf_file_path)
        print(f"Converted Markdown file saved at: {md_file_path}")
    except RuntimeError as e:
        print(e)