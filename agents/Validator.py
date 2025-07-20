import os
from strands import Agent, tool
from utils.novaModel import NOVA_MODEL
from strands_tools import retrieve
from pydantic import BaseModel
from enum import Enum
from memory.AgentsMemory import memory
import json

VALIDATION_PROMPT = """You are a Validator Agent responsible for validating clauses extracted from documents.
You will receive a set of clauses and a context in which the validation is being performed.
Your task is to validate each clause against the context and after comparing them, /
create a veredict if the proccess can continue or if the clauses need to be revised.
"""
class ValidationStatus(str, Enum):
    valid = "valid"
    invalid = "invalid"

class ValidationResult(BaseModel):
    clause: str
    status: ValidationStatus
    message: str

class ValidatorAgent:
    def __init__(self):
        self.agent = Agent(
            tools=[
                retrieve,
                self.compare
            ],
            model=NOVA_MODEL
        )

    @tool
    def compare(self, clauses: list, context: str) -> dict:
        """
        Compare the provided clauses against the context and validate them.

        Args:
            clauses (list): A list containing clauses to validate.
            context (str): The context in which the validation is being performed.

        Returns:
            dict: A JSON object with the validation status of each clause.
        """
        memory.set("actual_agent", "Validator")
        memory.set("actual_tool", "compare")
        if not clauses or not isinstance(clauses, list):
            
            return {"error": "No clauses provided for validation."}
        if not context:
            
            return {"error": "No context provided for validation."}

        # Create a prompt and use LLM to validate each clause
        validation_results = []
        for clause in clauses:
            prompt = f"Validate the following clause: {clause['clause_text']} in the context of: {context}"
            response = self.agent.structured_output(
                ValidationResult,
                prompt=prompt
            )
            validation_results.append({
                "clause": clause['clause_text'],
                "status": response.status,
                "message": response.message
            })

        # Return only the valid results
        validation_results = [result for result in validation_results if result['status'] == ValidationStatus.valid]
        if not validation_results:
            
            return {"error": "No valid clauses found after validation."}

        answer = "The following clauses are valid and can be used to create the final answer:\n"
        for result in validation_results:
            
            answer += f"- {result['clause']}\n"

        
        memory.set("valid_clauses", answer)
        return answer

    def __call__(self):
        memory.set("actual_agent", "Validator")
        return self.agent



@tool
def validate_agent(context: str) -> str:
    """
    Validate the clauses against the provided context.
    This function retrieves the clauses from memory and validates them using the ValidatorAgent.
    If the clauses are valid, it returns a message indicating that the validation was successful.
    If the clauses are invalid or if there is an error, it returns an appropriate error message.

    Args:
        context (str): The context in which the validation is being performed.

    Returns:
        str: A message indicating the validation status of the clauses.
    """

    memory.set("actual_agent", "Validator")
    clauses = memory.get("top_clauses") or []
    if not clauses:
        doc_name = memory.get("main_document")
        base_dir = os.getcwd()
        doc = os.path.join(base_dir, "clauses", doc_name) if doc_name else None
        if doc and os.path.exists(doc):
            print(f"Loading clauses from {doc}")
            with open(doc, "r") as f:
                clauses = json.load(f)
    if not clauses or not isinstance(clauses, list):
        return "No clauses provided for validation."
    if not context:
        return "No context provided for validation."
    
    validator_agent = ValidatorAgent()
    retrieved_content = validator_agent.agent.tool.retrieve(
        text=context,
        knowledgeBaseId=os.getenv("KNOWLEDGE_BASE_ID"),
        region=os.getenv("AWS_REGION", "us-east-1")
    )

          
    if not retrieved_content:
        return "No relevant information found for validation."
    
    print("Retrieved content for validation!")
    # print(retrieved_content['content'][0]['text'])

    result = validator_agent.agent.tool.compare(
        clauses=clauses,
        context=retrieved_content['content'][0]['text']
    )

    if not result:
        return "Validation failed due to an error in processing the clauses."
    
    return result

if __name__ == "__main__":
    # Example usage
    example_clauses = [
      {
        "section_title": "Pol\u00edtica Ambiental Capgemini",
        "clause_text": "Esta declara\u00e7\u00e3o de pol\u00edtica se aplica a todos os sites a partir dos quais a Capgemini opera, todos os funcion\u00e1rios, fornecedores e alian\u00e7as mantidas pela Capgemini.",
        "area": "compliance",
        "relevance": 0.9
      },
      {
        "section_title": "Pol\u00edtica Ambiental Capgemini",
        "clause_text": "Reconhecemos que nossas atividades de neg\u00f3cios t\u00eam impactos e oportunidades para o meio ambiente e estamos comprometidos em melhorar continuamente nosso desempenho ambiental em rela\u00e7\u00e3o a objetivos e metas relevantes (metas baseadas na ci\u00eancia, quando poss\u00edvel) assim como trabalhar com nossos clientes para ajud\u00e1-los a reduzir seus impactos ambientais.",
        "area": "operations",
        "relevance": 0.9
      },
      {
        "section_title": "Pol\u00edtica Ambiental Capgemini",
        "clause_text": "Estamos comprometidos em cumprir nossas obriga\u00e7\u00f5es de conformidade relacionadas aos impactos ambientais de nossas opera\u00e7\u00f5es e \u00e0 prote\u00e7\u00e3o do meio ambiente, incluindo a preven\u00e7\u00e3o da polui\u00e7\u00e3o por meio da ado\u00e7\u00e3o de controles apropriados.",
        "area": "compliance",
        "relevance": 0.9
      }
    ]
    memory.set("top_clauses", example_clauses)
    example_context = "O usuário quer saber sobre a política ambiental da Capgemini."
    validation_result = validate_agent(context=example_context)
    print(validation_result)  # This would be the output of the agent's processing