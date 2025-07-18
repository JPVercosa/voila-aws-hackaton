import os
import boto3
from typing import Any, Dict, List
from agents.Ingestion import ingestion_agent
from agents.Validator import validate_agent
from strands import Agent, tool
from dotenv import load_dotenv
from pydantic import BaseModel
from pprint import pprint
from agents.tools.agentsTools import check_status
from utils.novaModel import NOVA_MODEL

load_dotenv()

KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "default_kb_id")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "default_bucket_name")

ORCHESTRATOR_PROMPT = f"""
You are an Agent Orchestrator coordinating the creation of well-founded responses to user questions.
You will receive an instruction and must plan the execution of agents to answer the question.
You should start the execution by researching the most relevant document for the question in the Knowledge Base.
At this stage, do not generate a response; use the metadata to identify the most relevant document.
If this is not possible, return an error message stating that it was not possible to find the most relevant document.
You should consider the following available agents:

IngestionAgent: The agent responsible for orchestrating the ingestion of documents.
  - Receives an instruction containing the name of a document in PDF or Markdown format and processes it.
  - Can receive a summary of the question's context for better results.
  - Returns a JSON with the most relevant clauses extracted from the document and their areas.

ValidatorAgent: Agente responsável por validar as clausulas geradas pelo IngestionAgent.
  - Recebe um conjunto de clausulas e valida se elas estão corretas.
  - Retorna um JSON com o status de validação de cada clausula.
  - Pode receber um resumo do contexto da pergunta para obtenção de melhores resultados.
  - Retorna um JSON com o status de validação de cada clausula.

Variáveis Relevantes:
  - BUCKET_NAME: The name of the S3 bucket where the documents are stored = {BUCKET_NAME}
"""
teste="""
ReviewerAgent: Agente responsável por revisar as clausulas validadas pelo ValidatorAgent.
  - Recebe um conjunto de clausulas validadas e revisa-as.
  - Retorna um JSON com as clausulas revisadas e suas áreas.
  - Pode receber um resumo do contexto da pergunta para obtenção de melhores resultados.

CreatorAgent: Agente responsável por criar a resposta final com base nas clausulas revisadas.
  - Recebe um conjunto de clausulas revisadas e cria a resposta final.
  - Retorna a resposta final em formato JSON.

Você deve planejar a execução dos agentes de forma a otimizar o tempo de resposta e garantir que a resposta final seja precisa e completa.
"""

print(ORCHESTRATOR_PROMPT[-100:])

class DocumentList(BaseModel):
    documents: list[str]

class OrchestratorAgent():
    def __init__(self):
        self.agent = Agent(
            tools=[
                ingestion_agent,
                check_status,
                self.custom_retrieve,
                validate_agent
            ],
            model=NOVA_MODEL,
            system_prompt=ORCHESTRATOR_PROMPT
        )

    def filter_results_by_score(self, results: List[Dict[str, Any]], min_score: float) -> List[Dict[str, Any]]:
      """
      Filter results based on minimum score threshold.

      This function takes the raw results from a knowledge base query and removes
      any items that don't meet the minimum relevance score threshold.

      Args:
          results: List of retrieval results from Bedrock Knowledge Base
          min_score: Minimum score threshold (0.0-1.0). Only results with scores
              greater than or equal to this value will be returned.

      Returns:
          List of filtered results that meet or exceed the score threshold
      """
      return [result for result in results if result.get("score", 0.0) >= min_score]
    
    @tool
    def custom_retrieve(self, text: str, number_of_results: int = 10, score: float = 0.4) -> DocumentList:
        """
        Retrieve a list of documents from the knowledge base based on the provided text.

        Args:
            text (str): The text to search for in the knowledge base.
            number_of_results (int): The number of results to return. Default is 10.
            score (float): The minimum score threshold for results. Default is 0.4.

        Returns:
            documents_list: A list of documents that match the search criteria.
        """

        kb_id = os.getenv("KNOWLEDGE_BASE_ID")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        default_min_score = float(os.getenv("MIN_SCORE", "0.4"))
        min_score = score if score is not None else default_min_score

        bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime", region_name=region_name)
        
        # Perform retrieval
        response = bedrock_agent_runtime_client.retrieve(
            retrievalQuery={"text": text},
            knowledgeBaseId=kb_id,
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": 2},
            },
        )

        pprint(response)

         # Get and filter results
        all_results = response.get("retrievalResults", [])
        filtered_results = self.filter_results_by_score(all_results, min_score)
        documents_names = []
        for result in filtered_results:
            uri = result['location']['s3Location']['uri']
            documents_names.append(uri.split("/")[-1])  # Extract filename from S3 URI
        print(f"📄 Documents found: {documents_names}")
        return documents_names
    def __call__(self, instruction: str, kb_id: str, aws_region: str) -> dict:
        print(f"🤖 Orchestrator Agent - Processing instruction: {instruction}")
        completed_instruction = f"{instruction}\n\nUtilizando o Knowledge Base ID: {kb_id} na região {aws_region}"
        return self.agent(completed_instruction)


if __name__ == "__main__":
    
    orchestrator_agent = OrchestratorAgent()
    # print("Orchestrator Agent initialized with tools:", orchestrator_agent.tools)
    # Example usage
    result = orchestrator_agent("Valide as clausulas da política ambiental da Capgemini?", KNOWLEDGE_BASE_ID, AWS_REGION)
    print(result)  # This would be the output of the agent's processing


