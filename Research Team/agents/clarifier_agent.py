import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
import os

class ClarifierAgent:
    def __init__(self, kernel: sk.Kernel, prompts_path: str, service_id: str | None = None):
        self.kernel = kernel
        self.service_id = service_id
        
        # Get the full path to the ClarifyQuery.prompty file
        clarifier_prompt_file = os.path.join(prompts_path, "ClarifierAgent", "ClarifyQuery.prompty")
        
        # Check if the file exists
        if not os.path.exists(clarifier_prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {clarifier_prompt_file}")
        
        # Load the prompt content from the file
        with open(clarifier_prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Extract template from .prompty file
        template_start = prompt_content.find("template: |")
        template_format_start = prompt_content.find("template_format:")
        
        if template_start != -1 and template_format_start != -1:
            template_start += len("template: |")
            template = prompt_content[template_start:template_format_start].strip()
            
            # Create a function with the extracted template
            self.clarify_query_function = kernel.add_function(
                function_name="ClarifyQuery",
                plugin_name="ClarifierAgent", 
                prompt=template,
                description="Determines if a research query needs clarification"
            )
        else:
            raise ValueError("Could not extract template from the .prompty file")
            
        # Get the full path to the ClarifierQuestions.prompty file
        clarifier_questions_file = os.path.join(prompts_path, "ClarifierAgent", "ClarifierQuestions.prompty")
        
        # Check if the file exists
        if not os.path.exists(clarifier_questions_file):
            raise FileNotFoundError(f"Prompt file not found: {clarifier_questions_file}")
        
        # Load the prompt content from the file
        with open(clarifier_questions_file, 'r', encoding='utf-8') as f:
            questions_prompt_content = f.read()
        
        # Extract template from .prompty file
        template_start = questions_prompt_content.find("template: |")
        template_format_start = questions_prompt_content.find("template_format:")
        
        if template_start != -1 and template_format_start != -1:
            template_start += len("template: |")
            template = questions_prompt_content[template_start:template_format_start].strip()
            
            # Create a function with the extracted template
            self.clarifier_questions_function = kernel.add_function(
                function_name="ClarifierQuestions",
                plugin_name="ClarifierAgent", 
                prompt=template,
                description="Generates 3-5 clarifying questions for a research query"
            )
        else:
            raise ValueError("Could not extract template from the ClarifierQuestions.prompty file")

    async def clarify_query(self, user_query: str, initial_plan: str) -> str:
        arguments = KernelArguments(user_query=user_query, initial_plan=initial_plan)
        try:
            result = await self.kernel.invoke(
                self.clarify_query_function,
                arguments,
                service_id=self.service_id
            )
            response_text = str(result).strip()
            return response_text
        except Exception as e:
            print(f"Error invoking clarifier function: {e}")
            return "Error: Could not process clarification."
            
    async def generate_clarifying_questions(self, user_query: str) -> str:
        """Generate 3-5 clarifying questions for any research query."""
        arguments = KernelArguments(user_query=user_query)
        try:
            result = await self.kernel.invoke(
                self.clarifier_questions_function,
                arguments,
                service_id=self.service_id
            )
            questions_text = str(result).strip()
            return questions_text
        except Exception as e:
            print(f"Error generating clarifying questions: {e}")
            return "Error: Could not generate clarifying questions."

# Example usage (for testing)
async def _test_clarifier():
    kernel = sk.Kernel()
    # Configure AI service (e.g., OpenAI)
    # from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
    # import os
    # api_key = os.getenv("OPENAI_API_KEY")
    # org_id = os.getenv("OPENAI_ORG_ID")
    # service_id = "default_chat"
    # if not api_key:
    #     print("OpenAI API key not found for testing. Set OPENAI_API_KEY. Skipping clarifier test.")
    #     return
    # try:
    #     kernel.add_service(
    #         OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    #     )
    # except Exception as e:
    #     print(f"Error adding AI service for testing: {e}. Skipping clarifier test.")
    #     return

    # if not kernel.get_service(service_id):
    #     print(f"AI service '{service_id}' not configured for testing. Skipping clarifier test.")
    #     return
        
    prompts_root_dir = "../prompts"  # Adjust if running directly from agents directory
    # When testing, provide the service_id if it's expected by the constructor
    clarifier = ClarifierAgent(kernel, prompts_root_dir) # Add service_id here if testing

    test_query = "Tell me about quantum computing impact on finance."
    print(f"Generating clarifying questions for: \"{test_query}\"")
    # This test will fail if no AI service is configured above
    # clarifying_questions = await clarifier.generate_clarifying_questions(test_query)
    # print(f"\nClarifying Questions Result:\n{clarifying_questions}")
    
    test_plan = """1. [ResearchAgent] Search for general information on quantum computing.
2. [ResearchAgent] Search for applications of quantum computing in the finance sector.
3. [CritiqueAgent] Evaluate sources.
4. [SynthesiserAgent] Summarise findings.
5. [WriterAgent] Write a report."""

    print(f"Clarifying query: \"{test_query}\" with plan...")
    # This test will fail if no AI service is configured above
    # clarification_result = await clarifier.clarify_query(test_query, test_plan)
    # print(f"\nClarification Result:\n{clarification_result}")

    test_query_2 = "What is the capital of France?"
    test_plan_2 = "1. [ResearchAgent] Search for 'capital of France'. 2. [WriterAgent] State the capital."
    print(f"\nClarifying query: \"{test_query_2}\" with plan...")
    # This test will fail if no AI service is configured above
    # clarification_result_2 = await clarifier.clarify_query(test_query_2, test_plan_2)
    # print(f"\nClarification Result:\n{clarification_result_2}")
    print("\nNote: Clarifier tests are commented out by default. Uncomment and configure AI service to run.")


if __name__ == "__main__":
    # import asyncio
    # print("ClarifierAgent class defined. To test, uncomment the lines below,")
    # print("ensure you have an OpenAI API key configured, and run this script directly.")
    # asyncio.run(_test_clarifier())
    pass 