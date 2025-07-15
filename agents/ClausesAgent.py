import os
import json
from strands import Agent
from strands.models import BedrockModel
from pydantic import BaseModel, Field

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
    def __init__(self, file_title: str, context: str = ""):
        self.agent = Agent(model=NOVA_MODEL)
        self.file_title = file_title.replace(".md", ".json").replace(".json.json", ".json")
        self.context = context

    def analyze_sections(self) -> str:
        base_dir = os.getcwd()
        sections_dir = os.path.join(base_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)

        # Check for section files
        title_file = f"title_{self.file_title}"
        window_file = f"window_{self.file_title}"

        if title_file in os.listdir(sections_dir):
            sections_file = title_file
        elif window_file in os.listdir(sections_dir):
            sections_file = window_file
        else:
            return f"No sections found for {self.file_title}"

        with open(os.path.join(sections_dir, sections_file), "r", encoding="utf-8") as f:
            sections = json.load(f)

        rank_sections = []
        for section in sections:
            section_text = section.get('content', '').strip()
            if not section_text:
                print(f"Skipping empty section: {section.get('title', 'Untitled')}")
                continue

            prompt = (
                f"Analyze the section and generate clauses:\n\n{section_text}\n\n"
                "Each clause must have: text, area (from list), and relevance (0-1).\n"
                f"Areas: {', '.join(AREAS)}.\n"
                f"Context: {self.context if self.context else 'None'}"
            )

            try:
                result = self.agent.structured_output(Clauses, prompt)
            except Exception as e:
                print(f"Error analyzing section '{section.get('title', 'Untitled')}': {e}")
                continue

            if not result or not result.clauses:
                print(f"No clauses generated for section: {section.get('title', 'Untitled')}")
                continue

            for clause in result.clauses:
                rank_sections.append({
                    "title": section.get('title', 'Untitled'),
                    "clause_text": clause.clause_text,
                    "area": clause.area,
                    "relevance": clause.relevance
                })

        if not rank_sections:
            return "No clauses generated."

        rank_sections.sort(key=lambda x: x['relevance'], reverse=True)
        top_clauses = rank_sections[:10]

        return "\n".join(
            [f"Area: {c['area']} | Clause: {c['clause_text']} | Relevance: {c['relevance']}" for c in top_clauses]
        )

    def __call__(self) -> str:
        return self.analyze_sections()

# Example usage — NO tool wrapping needed!
if __name__ == "__main__":
    agent = ClausesAgent("230502_GenerativeAI_Guidelines_vF.json")
    result = agent()
    print(result)
