import os
from strands import tool

@tool
def check_status(self, document_name: str) -> str:
    """
    Check if the document has been processed.
    
    Args:
        document_name (str): The name of the document to check.
    
    Returns:
        str: A message indicating whether the document has been processed or not.
    """
    base_dir = os.getcwd()
    markdown_file = os.path.join(base_dir, "markdown", f"{document_name}.md")

    if os.path.exists(markdown_file):
        return f"Document {document_name} has been processed and is available in Markdown format."
    else:
        return f"Document {document_name} has not been processed yet."