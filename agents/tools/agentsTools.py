import os
from strands import tool
from memory.AgentsMemory import memory
from utils.normalizeNames import normalize_basename, make_md_name


@tool
def check_status(document_name: str) -> str:
    """
    Check if the document has already been processed and is available in Markdown format.
    This tool checks if a document with the given name exists in the markdown directory.
    
    Args:
        document_name (str): The name of the document to check.
    
    Returns:
        str: A message indicating whether the document has been processed or not.
    """
    memory.set("actual_tool", "check_status")
    base_dir = os.getcwd()
    base_name = normalize_basename(document_name)
    markdown_file = make_md_name(base_name)
    markdown_file_path = os.path.join(base_dir, "markdown", markdown_file)
    print(f"--------------- Checking status of {markdown_file_path} ---------------")

    
    if os.path.exists(markdown_file_path):
        return f"Document {markdown_file} has been processed and is available in Markdown format."
    else:
        return f"Document {markdown_file} has not been processed yet."
