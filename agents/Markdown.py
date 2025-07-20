import os
import boto3
from io import BytesIO
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import use_aws
from docling.document_converter import DocumentConverter, DocumentStream
from pprint import pprint
from pydantic import BaseModel
from memory.AgentsMemory import memory
from utils.normalizeNames import normalize_basename, make_pdf_name


# ---------------------------
# LLM configuration
# ---------------------------
NOVA_MODEL = BedrockModel(
    model_id="amazon.nova-pro-v1:0",
    region_name="us-east-1",
    temperature=0.2,
    top_p=0.9,
)

class FileMeta(BaseModel):
    base_name: str
    extension: str
    local_path: str

# ---------------------------
# PdfToMarkdownAgent as Class
# ---------------------------
class PdfToMarkdownAgent:
    def __init__(self):
        # Initialize tools
        self.s3_client = boto3.client("s3")
        self.agent = Agent(
            tools=[
                self.download_pdf_from_s3, 
                self.convert_pdf_save_md,
                use_aws
            ],
            model=NOVA_MODEL
        )

    @tool
    def download_pdf_from_s3(self, bucket: str, document_name: str) -> dict:
        """
        Download a PDF from S3 raw folder and save to a local tmp directory.
        Returns a dict with local_path and filename.

        Args:
            bucket (str): S3 bucket name.
            key (str): S3 object key (path to the PDF file).
        Returns:
            dict: Contains 'local_path' and 'filename' of the downloaded PDF.
        """
        memory.set("actual_agent", "Markdown")
        memory.set("actual_tool", "download_pdf_from_s3")
        base_dir = os.getcwd()
        tmp_dir = os.path.join(base_dir, "tmp")
        if not bucket or not document_name:
            
            return {"error": "Bucket and document_name must be provided."}

        key = f"raw/{document_name}"
        print(f"🔧 Downloading {key} from bucket {bucket}")

        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            pdf_bytes = response['Body'].read()
        except Exception as e:
            
            return {"error": f"Error downloading file from S3: {e}"}

        filename = key.rsplit("/", 1)[-1]
        local_path = os.path.join(tmp_dir, filename)

        try:
            os.makedirs(tmp_dir, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(pdf_bytes)
        except Exception as e:
            
            return {"error": f"Error saving file to local tmp: {e}"}

        print(f"📥 Downloaded {key} to {local_path} ({len(pdf_bytes)} bytes)")
        
        return {
            "local_path": local_path,
            "filename": filename
        }

    @tool
    def convert_pdf_save_md(self, local_path: str, filename: str) -> str:
        """
        Convert a local PDF file to Markdown and save it to a markdown directory with a .md extension.

        Args:
            local_path (str): Path to the local PDF file.
            filename (str): Name of the PDF file.

        Returns:
            str: Path to the saved Markdown file.
        """
        memory.set("actual_agent", "Markdown")
        memory.set("actual_tool", "convert_pdf_save_md")
        base_dir = os.getcwd()
        markdown_dir = os.path.join(base_dir, "markdown")

        print(f"🔄 Converting PDF: {local_path}")
        try:
            with open(local_path, "rb") as f:
                source_stream = DocumentStream(name=filename, stream=BytesIO(f.read()))
        except Exception as e:
            
            return f"Error reading PDF file: {e}"

        try:
            converter = DocumentConverter()
            result = converter.convert(source_stream).document
            markdown = result.export_to_markdown()
        except Exception as e:
            
            return f"Error converting PDF to Markdown: {e}"

        md_filename = filename.rsplit(".", 1)[0] + ".md"
        md_path = os.path.join(markdown_dir, md_filename)

        try:
            os.makedirs(markdown_dir, exist_ok=True)
            with open(md_path, "w", encoding="utf-8") as md_file:
                md_file.write(markdown)
        except Exception as e:
            
            return f"Error saving Markdown file: {e}"

        print(f"✅ Markdown saved to {md_path}")
        
        return f"Markdown saved to {md_path}"

    def __call__(self, query: str) -> str:
        """
        Allow the agent to be called like a function.
        """
        return self.agent(query)

# ---------------------------
# Wrap in Tool for other agents
# ---------------------------
@tool
def pdf_to_md_agent(document_name: str, bucket: str) -> str:
    """
    Tool to convert a PDF file from S3 to Markdown.
    This function orchestrates the download and conversion process.
    Then it saves the Markdown result file to a markdown directory with the same base filename and .md extension.

    Args:
        document_name (str): Title of the file to be processed without extension.
        bucket (str): Name of the S3 bucket where the PDF is stored.

    Returns:
        str: Result of the conversion process, including the path to the saved Markdown file.
    """
    memory.set("actual_agent", "Markdown")
    if not document_name or not bucket:
        return "Error: document_name and bucket must be provided."
    

    base = normalize_basename(document_name)
    pdf_name = make_pdf_name(base) 
    query = f"Download {pdf_name} from S3 bucket {bucket} and convert it to Markdown."
    print(f"🤖 PDF to MD Agent Tool - Markdown Agent")
    print(f"🔍 Processing query: {query}")
    pdf_md_agent = PdfToMarkdownAgent()
    result = pdf_md_agent(query)
    return str(result)

# ---------------------------
# Example Run
# ---------------------------
if __name__ == "__main__":
    example_query = (
        "Baixe o arquivo raw/230502_GenerativeAI_Guidelines_vF.pdf do bucket S3 cap-aws-hackaton-j3nf "
        "e converta o conteúdo em Markdown salvo em /tmp."
    )
    result = pdf_to_md_agent(example_query)
    pprint(result)
