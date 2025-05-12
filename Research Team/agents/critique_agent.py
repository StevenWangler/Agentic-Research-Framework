import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
import os

class CritiqueAgent:
    def __init__(self, kernel: sk.Kernel, prompts_path: str, service_id: str | None = None):
        self.kernel = kernel
        self.service_id = service_id
        
        # Get the full path to the CritiqueDocument.prompty file
        critique_prompt_file = os.path.join(prompts_path, "CritiqueAgent", "CritiqueDocument.prompty")
        
        # Check if the file exists
        if not os.path.exists(critique_prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {critique_prompt_file}")
        
        # Load the prompt content from the file
        with open(critique_prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Extract template from .prompty file
        template_start = prompt_content.find("template: |")
        template_format_start = prompt_content.find("template_format:")
        
        if template_start != -1 and template_format_start != -1:
            template_start += len("template: |")
            template = prompt_content[template_start:template_format_start].strip()
            
            # Create a function with the extracted template
            self.critique_document_function = kernel.add_function(
                function_name="CritiqueDocument",
                plugin_name="CritiqueAgent", 
                prompt=template,
                description="Critiques a research document based on task description"
            )
        else:
            raise ValueError("Could not extract template from the .prompty file")

    async def critique_document(self, research_task_description: str, research_document_text: str) -> str:
        """
        Critiques a single research document based on the original task and document content.
        Returns a structured critique string.
        """
        if not research_document_text or research_document_text.startswith("Error:"):
            # Return a structured error message or an indication that critique is skipped
            return f"Critique Skipped for Task: {research_task_description}\nReason: Document content is empty or an error message from a previous step.\nDocument Content Provided: {research_document_text[:100]}..."

        arguments = KernelArguments(
            research_task_description=research_task_description,
            research_document_text=research_document_text
        )
        try:
            result = await self.kernel.invoke(
                self.critique_document_function,
                arguments,
                service_id=self.service_id
            )
            return str(result).strip()
        except Exception as e:
            print(f"Error invoking critique function for task '{research_task_description}': {e}")
            return f"Error: Could not critique document for task: {research_task_description}. Details: {str(e)}"

# Example usage (for testing)
async def _test_critique_agent():
    kernel = sk.Kernel()
    # Configure AI service (e.g., OpenAI)
    # from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
    # import os
    # api_key = os.getenv("OPENAI_API_KEY")
    # org_id = os.getenv("OPENAI_ORG_ID")
    # service_id = "default_chat"
    # if not api_key:
    #     print("OpenAI API key not found. Set OPENAI_API_KEY. Skipping critique agent test.")
    #     return
    # try:
    #     kernel.add_service(
    #         OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    #     )
    # except Exception as e:
    #     print(f"Error adding AI service for testing: {e}. Skipping critique agent test.")
    #     return

    # if not kernel.get_service(service_id):
    #     print(f"AI service '{service_id}' not configured. Skipping critique agent test.")
    #     return
        
    prompts_root_dir = "../prompts" 
    # When testing, provide the service_id if it's expected by the constructor
    critique_agent = CritiqueAgent(kernel, prompts_root_dir) # Add service_id here if testing

    sample_task = "Explain the concept of photosynthesis."
    sample_document = """Photosynthesis is a process used by plants, algae, and some bacteria to convert light energy into chemical energy, through a process that involves water and carbon dioxide, releasing oxygen as a byproduct. This chemical energy is stored in carbohydrate molecules, such as sugars, which are synthesized from carbon dioxide and water."""

    print(f"Critiquing document for task: \"{sample_task}\"")
    # This test will fail if no AI service is configured above
    # critique_result = await critique_agent.critique_document(sample_task, sample_document)
    # print(f"\nCritique Result:\n{critique_result}")

    error_document_task = "Investigate the effects of cosmic rays on lunar soil."
    error_document_content = "Error: Could not conduct research for task: Investigate the effects of cosmic rays on lunar soil."
    print(f"\nCritiquing error document for task: \"{error_document_task}\"")
    # This test will also be handled by the agent's internal check
    # critique_error_result = await critique_agent.critique_document(error_document_task, error_document_content)
    # print(f"\nCritique for error document:\n{critique_error_result}")
    print("\nNote: Critique Agent tests are commented out by default. Uncomment and configure AI service to run.")

if __name__ == "__main__":
    # import asyncio
    # print("CritiqueAgent class defined. To test, uncomment lines in _test_critique_agent,")
    # print("ensure you have an OpenAI API key configured, and run this script directly.")
    # asyncio.run(_test_critique_agent())
    pass 