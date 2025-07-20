import os
import json
from strands import Agent, tool
from strands.models import BedrockModel
from utils.normalizeNames import normalize_basename, make_md_name
from memory.AgentsMemory import memory

# ---------------------------
# LLM configuration
# ---------------------------
NOVA_MODEL = BedrockModel(
    model_id="amazon.nova-pro-v1:0",
    region_name="us-east-1",
    temperature=0.2,
    top_p=0.9,
)

class SplitterAgent:
    def __init__(self):
        self.agent = Agent(
            tools=[
                self.split_sections_by_title, 
                self.split_sections_by_sliding_window, 
                self.count_words_and_titles
            ],
            model=NOVA_MODEL
        )

    @tool
    def split_sections_by_title(self, document_name: str) -> str:
        """
        Split the document into sections based on Markdown titles.
        
        Args:
            document_name (str): The name of the Markdown file to be processed.
        Returns:
            str: The result of the splitting operation, including the path to the saved sections file.
        """
        memory.set("actual_agent", "Splitter")
        memory.set("actual_tool", "split_sections_by_title")
        if not document_name:
            
            return "Name of the file is not provided."

        base_dir = os.getcwd()
        markdown_dir = os.path.join(base_dir, "markdown")
        sections_dir = os.path.join(base_dir, "sections")

        print(f"🔧 Splitting document by titles: {document_name}")

        try:
            # Read the file content
            with open(os.path.join(markdown_dir, document_name), "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            
            return f"File {document_name} not found in {markdown_dir}."
        except Exception as e:
            
            return f"Error reading file: {e}"

        if not text.strip():
            
            return "File is empty."
        
        sections = []
        lines = text.splitlines()
        current_section = None

        for line in lines:
            if line.startswith("## "):
                if current_section:
                    sections.append(current_section)
                current_section = {"title": line[3:].strip(), "content": ""}
            elif current_section is not None:
                current_section["content"] += line.rstrip() + "\n"
        if current_section:
            sections.append(current_section)

        if not sections:
            
            return "No sections found in the document."

        try:
            os.makedirs(sections_dir, exist_ok=True)
            base_name = normalize_basename(document_name)
            sections_file = os.path.join(sections_dir, f"title_{base_name}.json")
            # Save JSON sections to a file
            with open(sections_file, "w", encoding="utf-8") as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
        except Exception as e:
            
            return f"Error saving sections to file: {e}"

        
        return "Sections saved to " + sections_file

    @tool
    def split_sections_by_sliding_window(self, document_name: str, window_size: int, overlap: int) -> str:
        """
        Split the text into sections using a sliding window approach with overlap.

        Args:
            window_size (int): The size of the sliding window.
            overlap (int): The number of characters each window should overlap with the previous one.

        Returns:
            str: The result of the splitting operation, including the path to the saved sections file.
        """
        memory.set("actual_agent", "Splitter")
        memory.set("actual_tool", "split_sections_by_sliding_window")
        if not document_name:
            
            return "Name of the file is not provided."
        
        print(f"🔧 Splitting document by sliding window: {document_name} with window size {window_size} and overlap {overlap}")

        base_dir = os.getcwd()
        markdown_dir = os.path.join(base_dir, "markdown")
        sections_dir = os.path.join(base_dir, "sections")

        try:
            with open(os.path.join(markdown_dir, document_name), "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            
            return f"File {document_name} not found in {markdown_dir}."
        except Exception as e:
            
            return f"Error reading file: {e}"

        if not text.strip():
            
            return "File is empty."

        sections = []
        step_size = window_size - overlap
        if step_size <= 0:
            
            return "Overlap must be smaller than window size."

        for i in range(0, len(text), step_size):
            section = {
                "title": f"Section {i // step_size + 1}",
                "content": text[i:i + window_size]
            }
            sections.append(section)

        try:
            os.makedirs(sections_dir, exist_ok=True)
            base_name = normalize_basename(document_name)
            sections_file = os.path.join(sections_dir, f"window_{base_name}.json")
            with open(sections_file, "w", encoding="utf-8") as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
        except Exception as e:
            
            return f"Error saving sections to file: {e}"

        
        return "Sections saved to " + sections_file

    @tool
    def count_words_and_titles(self, document_name: str) -> tuple[int, int]:
        """
        Count the number of words and titles in the text.

        Returns:
            tuple[int, int]: A tuple containing the word count and title count.
        """
        memory.set("actual_agent", "Splitter")
        memory.set("actual_tool", "count_words_and_titles")
        if not document_name:
            
            return 0, 0
        
        print(f"🔧 Counting words and titles in document: {document_name}")

        base_dir = os.getcwd()
        markdown_dir = os.path.join(base_dir, "markdown")

        try:
            with open(os.path.join(markdown_dir, document_name), "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            
            return 0, 0
        except Exception:
            
            return 0, 0

        if not text.strip():
            return 0, 0

        word_count = len(text.split())
        title_count = text.count("## ")
        
        return word_count, title_count

    def __call__(self, query: str) -> str:
        """
        Allows the agent to be called with a query.
        """
        return self.agent(query)

@tool
def splitter_agent(document_name: str) -> str:
    """
    Tool to split a document into sections based on titles or sliding window.
    It must receive the name of the document to be processed.
    
    Args:
        document_name (str): The name of the document to be processed.
    Returns:
        str: Result of the splitting operation.
    """
    memory.set("actual_agent", "Splitter")

    if not document_name:
        return "Error: document_name must be provided."
    
    
    base = normalize_basename(document_name)
    document_name = make_md_name(base)

    # Check if the file exists
    base_dir = os.getcwd()
    markdown_dir = os.path.join(base_dir, "markdown")
    if not os.path.exists(os.path.join(markdown_dir, document_name)):
        return f"Error: Document {document_name} does not exist in {markdown_dir}."
    
    splitter = SplitterAgent()
    query = f"Split the document {document_name} into sections. Use titles or sliding window as appropriate."
    print(f"🤖 Splitter Agent Tool - Splitting document: {document_name}")
    print(f"🔍 Processing query: {query}")
    result = splitter(query)
    return str(result)

# Example usage
if __name__ == "__main__":
    query = "Analise o texto e faça a divisão da melhor forma possível."
    document_name = "230502_GenerativeAI_Guidelines_vF.md"
    result = splitter_agent(query, document_name)
    print(result)
