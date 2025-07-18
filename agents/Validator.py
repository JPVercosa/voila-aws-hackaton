import os
from strands import Agent, tool
from utils.novaModel import NOVA_MODEL
from strands_tools import retrieve
from pydantic import BaseModel

VALIDATION_PROMPT = """You are a Validator Agent responsible for validating clauses extracted from documents.
You will receive a set of clauses and a context in which the validation is being performed.
Your task is to validate each clause against the context and after comparing them, /
create a veredict if the proccess can continue or if the clauses need to be revised.
"""

class ValidationResult(BaseModel):
    clause: str
    status: str
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
        return validation_results

    def __call__(self):
        return self.agent



@tool
def validate_agent(clauses: dict, context: str) -> str:
    """
    Receives a set of clauses and the context in which the validation is being performed.
    Validates the clauses and returns a message indicating the validation status.

    Args:
        clauses (list[dict]): A list of dictionaries containing clauses to validate.
        context (str): The context in which the validation is being performed.

    Returns:
        str: A message indicating the validation status of the clauses.
    """

    # print(clauses)

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
      },
      {
        "section_title": "Pol\u00edtica Ambiental Capgemini",
        "clause_text": "Identifiquem e implementem iniciativas de economia de energia em nossas instala\u00e7\u00f5es para reduzir o consumo de energia do Grupo, apoiando a transi\u00e7\u00e3o do Grupo para energia renov\u00e1vel e ajudar a redu\u00e7\u00e3o as emiss\u00f5es de GEE associados.",
        "area": "operations",
        "relevance": 0.9
      },
      {
        "section_title": "Pol\u00edtica Ambiental Capgemini",
        "clause_text": "Tenham processos de compras que garantam que nossos fornecedores e parceiros de neg\u00f3cios forne\u00e7am produtos e servi\u00e7os que nos ajudem a atingir os objetivos ambientais do Grupo, particularmente em rela\u00e7\u00e3o \u00e0s emiss\u00f5es de carbono, redu\u00e7\u00e3o do consumo de energia e \u00e1gua, redu\u00e7\u00e3o do impacto na biodiversidade e minimiza\u00e7\u00e3o do desperd\u00edcio adotando os princ\u00edpios da circularidade.",
        "area": "procurement",
        "relevance": 0.9
      },
      {
        "section_title": "Pol\u00edtica Ambiental Capgemini",
        "clause_text": "Gerimos a implementa\u00e7\u00e3o desta pol\u00edtica ambiental e os nossos impactos ambientais atrav\u00e9s do nosso sistema de gest\u00e3o ambiental global que est\u00e1 certificado na norma ISO 14001.",
        "area": "operations",
        "relevance": 0.9
      },
      {
        "section_title": "Pol\u00edtica Ambiental Capgemini",
        "clause_text": "O desempenho em rela\u00e7\u00e3o aos nossos objetivos e metas ser\u00e1 revisado pelo menos anualmente e reportado publicamente em nosso Relat\u00f3rio Financeiro Anual e em quaisquer Relat\u00f3rios de Sustentabilidade associados. Esta Pol\u00edtica Ambiental ser\u00e1 revista pelo menos uma vez por ano.",
        "area": "operations",
        "relevance": 0.9
      },
      {
        "section_title": "Adriana Gomes Guimaraes Oestreich",
        "clause_text": "Esta declara\u00e7\u00e3o de pol\u00edtica se aplica a todos os sites a partir dos quais a Capgemini opera, todos os funcion\u00e1rios, fornecedores e alian\u00e7as mantidas pela Capgemini.",
        "area": "compliance",
        "relevance": 0.9
      },
      {
        "section_title": "Adriana Gomes Guimaraes Oestreich",
        "clause_text": "Reconhecemos que nossas atividades de neg\u00f3cios t\u00eam impactos e oportunidades para o meio ambiente e estamos comprometidos em melhorar continuamente nosso desempenho ambiental em rela\u00e7\u00e3o a objetivos e metas relevantes (metas baseadas na ci\u00eancia, quando poss\u00edvel) assim como trabalhar com nossos clientes para ajud\u00e1-los a reduzir seus impactos ambientais.",
        "area": "operations",
        "relevance": 0.9
      },
      {
        "section_title": "Adriana Gomes Guimaraes Oestreich",
        "clause_text": "Estamos comprometidos em cumprir nossas obriga\u00e7\u00f5es de conformidade relacionadas aos impactos ambientais de nossas opera\u00e7\u00f5es e \u00e0 prote\u00e7\u00e3o do meio ambiente, incluindo a preven\u00e7\u00e3o da polui\u00e7\u00e3o por meio da ado\u00e7\u00e3o de controles apropriados.",
        "area": "compliance",
        "relevance": 0.9
      }
    ]

    example_context = "O usuário quer saber sobre a política ambiental da Capgemini."
    validation_result = validate_agent(clauses=example_clauses, context=example_context)
    print(validation_result)  # This would be the output of the agent's processing