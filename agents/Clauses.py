from email.mime import base
import os
import json
from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from pprint import pprint
from utils.normalizeNames import normalize_basename, make_sections_name

# ---------------------------
# LLM configuration
# ---------------------------
NOVA_MODEL = BedrockModel(
    model_id="amazon.nova-pro-v1:0",
    region_name="us-east-1",
    temperature=0.2,
    top_p=0.9,
)

AREAS = {
    "hr", "security", "privacy", "compliance", "operations",
    "finance", "legal", "risk_management", "it", "procurement",
    "health_safety", "ethics", "training", "customer_relations",
}

class Clause(BaseModel):
    clause_text: str
    area: str = Field(..., description="Valid area according to enum AREAS")
    relevance: float = Field(..., description="Relevance score 0-1")

class Clauses(BaseModel):
    clauses: list[Clause]

class ClausesAgent:
    def __init__(self):
        self.agent = Agent(model=NOVA_MODEL)
        

    def analyze_sections(self, document_name: str, chosen_file: str, context: str = "") -> dict:
        base_dir = os.getcwd()
        sections_dir = os.path.join(base_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)

        print(f"🤖 Clauses Creator Agent - Analyze Sections")
        print(f"🔍 Document Name: {document_name}, Chosen File: {chosen_file}, Context: {context[:30]}" )
        with open(os.path.join(sections_dir, chosen_file), "r", encoding="utf-8") as f:
            sections = json.load(f)

        rank_sections = []
        for section in sections:
            section_text = section.get('content', '').strip()
            if not section_text:
                continue

            prompt = (
                "Analyze the section and generate clauses:\n\n"
                f"Section: {section_text}\n\n"
                "Each clause must have: text, area (from list), and relevance (0-1).\n"
                f"Areas: {', '.join(AREAS)}.\n"
                f"Context: {context if context else 'No context provided.'}\n\n"
            )

            try:
                result = self.agent.structured_output(Clauses, prompt)
            except Exception as e:
                print(f"🔍 Error processing section: {e}")
                continue

            if not result or not result.clauses:
                print(f"🔍 No clauses generated for section: {section.get('title', 'Untitled')}")
                continue

            for clause in result.clauses:
                rank_sections.append({
                    "section_title": section.get('title', 'Untitled'),
                    "clause_text": clause.clause_text,
                    "area": clause.area,
                    "relevance": clause.relevance
                })

        if not rank_sections:
            print(f"🔍 No clauses generated.")
            return {"file": document_name, "clauses": []}

        rank_sections.sort(key=lambda x: x['relevance'], reverse=True)
        top_clauses = rank_sections[:10]

        result = {"file": document_name, "clauses": top_clauses}
        clauses = result.get("clauses", [])

        if clauses:
            # Save the top clauses to a JSON file
            os.makedirs(os.path.join(base_dir, "clauses"), exist_ok=True)
            clauses_file = os.path.join(base_dir, "clauses", f"{document_name}.json")
            with open(clauses_file, "w", encoding="utf-8") as f:
                json.dump(top_clauses, f, indent=2)
            
        
        return {"file": document_name, "clauses": top_clauses}

    def __call__(self, document_name: str, chosen_file: str, context: str = "") -> str:
        result = self.analyze_sections(document_name, chosen_file, context)
        return json.dumps(result, indent=2)
    
@tool
def clauses_agent(document_name: str, context: str = "") -> str:
    """
    Analyze sections of a document and extract relevant clauses.
    The context can be provided to enhance the analysis.

    Args:
        document_name (str): Name of the document to analyze.
        context (str): Optional context for analysis.

    Returns:
        str: JSON string with extracted clauses.
    """
    if not document_name:
        return "Document name is required."
    
    base = normalize_basename(document_name)
    title_file = make_sections_name(base, "title")    # e.g. title_My_File.json
    window_file = make_sections_name(base, "window")  # e.g. window_My_File.json    

    base_dir = os.getcwd()
    sections_dir = os.path.join(base_dir, "sections")
    title_path = os.path.join(sections_dir, title_file)
    window_path = os.path.join(sections_dir, window_file)

    if os.path.exists(title_path):
        chosen_file = title_file
        print(f"✅ Using title sections: {title_file}")
    elif os.path.exists(window_path):
        chosen_file = window_file
        print(f"✅ Using window sections: {window_file}")
    else:
        return f"Error: No sections found for base name '{base}'. Expected {title_file} or {window_file} in {sections_dir}."

    agent = ClausesAgent()
    return agent(base, chosen_file, context)

# Example usage — NO tool wrapping needed!
if __name__ == "__main__":
    # agent = ClausesAgent("230502_GenerativeAI_Guidelines_vF.json")
    # result = agent()
    # pprint(result)
    example_file = "230502_GenerativeAI_Guidelines_vF.json"
    result = clauses_agent(example_file)
    pprint(result)