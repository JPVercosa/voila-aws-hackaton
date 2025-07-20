from strands import Agent, tool
from utils.novaModel import NOVA_MODEL
from memory.AgentsMemory import memory


class CreatorAgent:
    def __init__(self):
        self.agent = Agent(
            model=NOVA_MODEL
        )

    def create_response(self) -> str:
        """
        Create the final response based on the validated clauses and the user's question.
        The function uses the memory to retrieve the validated clauses and the user's question.

        Returns:
            str: The final response.
        """
        print("🤖 Creator Agent - Create Response")
        memory.set("actual_agent", "Creator")
        memory.set("actual_tool", "create_response")
        validated_clauses = memory.get("valid_clauses") or None
    

        if not validated_clauses:
            
            print("❌ No validated clauses provided for creating a response.")
            return "No validated clauses provided for creating a response."

        user_input = memory.get("user_input") or None
        if not user_input:
            print("❌ User question not found in memory.")
            return "User question not found in memory."
        
        document_name = memory.get("main_document") or ""
        
        # Create a prompt and use LLM to generate the final response
        prompt = f"Create a response to the following question: {user_input}\n\n"
        prompt += f"Based on the following validated clauses: \n {validated_clauses if validated_clauses else ''}"
        prompt += f"In the end of your response, refer to the document: {document_name}\n\n"
        response = self.agent(prompt)
        
        return response
    
@tool
def create_answer() -> str:
    """
    Create the final answer using the CreatorAgent.
    This functions use memory to retrieve the validated clauses and the user's question.
    And creates the final answer.

    Returns:
        str: The final answer.
    """
    memory.set("actual_agent", "Creator")
    memory.set("actual_tool", "create_answer")
    creator_agent = CreatorAgent()
    response = creator_agent.create_response()
    
    if not response:
        return "Error with create_answer tool Agent. No response generated."

    print(f"🤖 Creator Agent - Response: {response}")
    return response