from agents.Markdown import pdf_to_md_agent
from agents.Splitter import splitter_agent
from agents.Clauses import clauses_agent
from strands import Agent, tool
from strands.models import BedrockModel
import os


NOVA_MODEL = BedrockModel(
    model_id="amazon.nova-pro-v1:0",
    region_name="us-east-1",
    temperature=0.2,
    top_p=0.9,
)

INGESTION_PROMPT = """
You are an Ingestion Agent that orchestrates the ingestion of documents.
You will receive a document in PDF or Markdown format, and your task is to process it.
Based on the document, you will:
1. Convert the document to Markdown format if it is not already in that format.
2. Split the document into sections based on titles.
3. Analyze the sections to extract relevant clauses and their areas.

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
"""

class IngestionAgent(Agent):
    def __init__(self):
        super().__init__(
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

    
if __name__ == "__main__":
    ingestion_agent = IngestionAgent()
    # Example usage
    result = ingestion_agent("Download raw/Politica_Ambiental_2024.pdf from S3 bucket cap-aws-hackaton-j3nf and process it.")
    print(result)
    # Note: Replace "path/to/document.pdf" with the actual path to your document.