import os
import json
from strands import Agent, tool
from strands.models import BedrockModel

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
    def __init__(self, query: str, file_title: str):
        self.agent = Agent(
            tools=[
                self.split_sections_by_title, 
                # self.split_sections_by_sliding_window, 
                self.count_words_and_titles
            ],
            model=NOVA_MODEL
        )
        self.file_title = file_title if ".md" in file_title else f"{file_title}.md"

    @tool
    def split_sections_by_title(self) -> str:
        """
        Split the document into sections based on Markdown titles.
        
        Returns:
            str: The result of the splitting operation, including the path to the saved sections file.
        """
        if not self.file_title:
            return "Name of the file is not provided."

        base_dir = os.getcwd()
        markdown_dir = os.path.join(base_dir, "markdown")
        sections_dir = os.path.join(base_dir, "sections")

        try:
            # Read the file content
            with open(os.path.join(markdown_dir, self.file_title), "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            return f"File {self.file_title} not found in {markdown_dir}."
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
            base_name = os.path.splitext(self.file_title)[0]
            sections_file = os.path.join(sections_dir, f"title_{base_name}.json")
            # Save JSON sections to a file
            with open(sections_file, "w", encoding="utf-8") as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error saving sections to file: {e}"

        return "Sections saved to " + sections_file

    @tool
    def split_sections_by_sliding_window(self, window_size: int, overlap: int) -> str:
        """
        Split the text into sections using a sliding window approach with overlap.

        Args:
            window_size (int): The size of the sliding window.
            overlap (int): The number of characters each window should overlap with the previous one.

        Returns:
            str: The result of the splitting operation, including the path to the saved sections file.
        """
        if not self.file_title:
            return "Name of the file is not provided."

        base_dir = os.getcwd()
        markdown_dir = os.path.join(base_dir, "markdown")
        sections_dir = os.path.join(base_dir, "sections")

        try:
            with open(os.path.join(markdown_dir, self.file_title), "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            return f"File {self.file_title} not found in {markdown_dir}."
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
            base_name = os.path.splitext(self.file_title)[0]
            sections_file = os.path.join(sections_dir, f"window_{base_name}.json")
            with open(sections_file, "w", encoding="utf-8") as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error saving sections to file: {e}"

        return "Sections saved to " + sections_file

    @tool
    def count_words_and_titles(self) -> tuple[int, int]:
        """
        Count the number of words and titles in the text.

        Returns:
            tuple[int, int]: A tuple containing the word count and title count.
        """
        if not self.file_title:
            return 0, 0

        base_dir = os.getcwd()
        markdown_dir = os.path.join(base_dir, "markdown")

        try:
            with open(os.path.join(markdown_dir, self.file_title), "r", encoding="utf-8") as f:
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
def splitter_agent(query: str, document_name: str) -> str:
    """
    Tool to split a document into sections based on titles or sliding window.
    Args:
        query (str): The query to process.
        document_name (str): The name of the document to be processed.
    Returns:
        str: Result of the splitting operation.
    """
    splitter = SplitterAgent(query, file_title=document_name)
    result = splitter(query)
    return str(result)

# Example usage
if __name__ == "__main__":
    query = "Analise o texto e faça a divisão da melhor forma possível."
    document_name = "230502_GenerativeAI_Guidelines_vF.md"
    result = splitter_agent(query, document_name)
    print(result)
