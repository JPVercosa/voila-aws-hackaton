from agents.Markdown import pdf_to_md_agent
from agents.Splitter import splitter_agent
from agents.Clauses import clauses_agent
from strands import Agent, tool
from strands.models import BedrockModel
from utils.normalizeNames import normalize_basename, make_pdf_name
import os


NOVA_MODEL = BedrockModel(
    model_id="amazon.nova-pro-v1:0",
    region_name="us-east-1",
    temperature=0.2,
    top_p=0.9,
)

INGESTION_PROMPT = """
You are an Ingestion Agent that orchestrates the ingestion of documents.
You will receive a instruction containing the name of a document in PDF or Markdown format, and your task is to process it.
Based on the document, you will:
1. Check if the document is already in Markdown format.
2. Convert the document to Markdown format if it is not already in that format.
3. Split the document into sections based on titles.
4. Analyze the sections to extract relevant clauses and their areas.

You will return a JSON object with the following structure:
{
    "file": "document_name",
    "clauses": [
        {
            "clause_text": "Text of the clause",
            "area": "Relevant area",
            "relevance": 0.85
        },
        ...
    ]
}

The prompt can also contain the context of the document, which you can use to pass to the tools if needed.
"""

class IngestionAgent():
    def __init__(self):
        self.agent = Agent(
            tools=[
                self.check_status,
                pdf_to_md_agent,
                splitter_agent,
                clauses_agent
            ],
            model=NOVA_MODEL,
            system_prompt=INGESTION_PROMPT
        )
    
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
        
    def __call__(self, instruction: str) -> dict:
        return self.agent(instruction)

@tool
def ingestion_agent(instruction: str, document_name: str, bucket_name: str, context: str) -> dict:
    """
    Ingest a document based on the provided instruction.
    The ingestion process includes downloading a PDF or Markdown document, converting it to Markdown if necessary,
    splitting it into sections, and extracting relevant clauses.

    Args:
        instruction (str): Instruction containing the document name and processing details.
        document_name (str): The name of the document to be ingested.
        bucket_name (str): The name of the S3 bucket where the document is stored.
        context (str): The context to be used for processing the document.

    Returns:
        dict: JSON object with the name of the processed document and a list of more relevant clauses based on the context provided and their areas.
    """
    base = normalize_basename(document_name)
    pdf_name = make_pdf_name(base)
    instruction = f"Download {pdf_name} from S3 bucket {bucket_name} and process it. Context: {context}"
    print(f"🤖 Ingestion Agent Tool - Ingestion Agent")
    print(f"🔍 Processing query: {instruction}")
    ingestion_agent = IngestionAgent()
    result = ingestion_agent(instruction)
    return result

if __name__ == "__main__":
    ingestion_agent = IngestionAgent()
    # Example usage
    result = ingestion_agent("Download raw/Politica_Ambiental_2024.pdf from S3 bucket cap-aws-hackaton-j3nf and process it.")
    print(result)
    # Note: Replace "path/to/document.pdf" with the actual path to your document.