import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from typing import List, Dict
import os

class SynthesiserAgent:
    def __init__(self, kernel: sk.Kernel, prompts_path: str, service_id: str | None = None):
        self.kernel = kernel
        self.service_id = service_id
        
        # Get the full path to the SynthesiseCritiques.prompty file
        synthesiser_prompt_file = os.path.join(prompts_path, "SynthesiserAgent", "SynthesiseCritiques.prompty")
        
        # Check if the file exists
        if not os.path.exists(synthesiser_prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {synthesiser_prompt_file}")
        
        # Load the prompt content from the file
        with open(synthesiser_prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Extract template from .prompty file
        template_start = prompt_content.find("template: |")
        template_format_start = prompt_content.find("template_format:")
        
        if template_start != -1 and template_format_start != -1:
            template_start += len("template: |")
            template = prompt_content[template_start:template_format_start].strip()
            
            # Create a function with the extracted template
            self.synthesise_critiques_function = kernel.add_function(
                function_name="SynthesiseCritiques",
                plugin_name="SynthesiserAgent", 
                prompt=template,
                description="Synthesizes information from critiqued research documents"
            )
        else:
            raise ValueError("Could not extract template from the .prompty file")

    def _format_critiques_for_prompt(self, critiqued_documents: List[Dict[str, str]]) -> str:
        formatted_string = ""
        if not critiqued_documents:
            return "No critiqued documents were provided.\n"
            
        for i, item in enumerate(critiqued_documents):
            formatted_string += f"Critiqued Document {i+1}:\n"
            formatted_string += f"Original Task: {item.get('original_task', 'N/A')}\n"
            # The 'critique_text' is the full structured critique from CritiqueAgent
            critique_content = item.get('critique_text', 'N/A')
            if critique_content.startswith("Critique Skipped for Task"):
                formatted_string += f"Critique Status: Skipped or Errored\nDetails: {critique_content}\n"
            else:
                formatted_string += f"Critique:\n{critique_content}\n"
            formatted_string += "---\n"
        return formatted_string

    async def synthesise_research(self, overall_user_query: str, critiqued_documents: List[Dict[str, str]]) -> str:
        """
        Synthesizes information from a list of critiqued documents.
        """
        if not critiqued_documents:
            return "Error: No critiqued documents provided for synthesis."

        formatted_critiques_str = self._format_critiques_for_prompt(critiqued_documents)
        
        # Handle case where all critiques might have been skipped
        if all("Critique Status: Skipped or Errored" in f_item for f_item in formatted_critiques_str.split("---")) and critiqued_documents:
             return f"Error: All document critiques were skipped or resulted in errors. Cannot synthesise from: {formatted_critiques_str}"

        arguments = KernelArguments(
            overall_user_query=overall_user_query,
            formatted_critiques=formatted_critiques_str
        )
        
        try:
            result = await self.kernel.invoke(
                self.synthesise_critiques_function,
                arguments,
                service_id=self.service_id
            )
            return str(result).strip()
        except Exception as e:
            error_message = f"Error invoking synthesiser function: {e}. Query: {overall_user_query}"
            print(error_message)
            return f"Error: Could not synthesise research. Details: {str(e)}"

# Example usage (for testing)
async def _test_synthesiser_agent():
    kernel = sk.Kernel()
    # Configure AI service (e.g., OpenAI)
    # from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
    # import os
    # api_key = os.getenv("OPENAI_API_KEY")
    # org_id = os.getenv("OPENAI_ORG_ID")
    # service_id = "default_chat" 
    # if not api_key:
    #     print("OpenAI API key not found. Set OPENAI_API_KEY. Skipping synthesiser test.")
    #     return
    # try:
    #     kernel.add_service(
    #         OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    #     )
    # except Exception as e:
    #     print(f"Error adding AI service for testing: {e}. Skipping synthesiser test.")
    #     return
    # if not kernel.get_service(service_id):
    #     print(f"AI service '{service_id}' not configured. Skipping synthesiser agent test.")
    #     return

    prompts_root_dir = "../prompts"
    # When testing, provide the service_id if it's expected by the constructor
    synthesiser = SynthesiserAgent(kernel, prompts_root_dir) # Add service_id here if testing

    sample_overall_query = "What are the primary concerns regarding microplastic pollution and potential solutions?"

    sample_critiqued_docs = [
        {
            "original_task": "Summarize sources of microplastic pollution.",
            "critique_text": """Relevance to Task: High
Key Points Covered:
- Industrial discharge
- breakdown of larger plastic debris
- synthetic textiles (washing clothes)
Potential Gaps or Biases: Does not mention tire wear.
Overall Quality Assessment: Good
Concise Summary of this Document: Document outlines major sources like industrial waste, plastic degradation, and textiles. It's a good overview but misses tire particles."""
        },
        {
            "original_task": "Outline the ecological impact of microplastics.",
            "critique_text": """Relevance to Task: High
Key Points Covered:
- Ingestion by marine life
- Potential for bioaccumulation in food chain
- Chemical leaching from plastics
Potential Gaps or Biases: Focuses heavily on marine; less on terrestrial or freshwater.
Overall Quality Assessment: Excellent
Concise Summary of this Document: This document thoroughly details how microplastics affect marine ecosystems through ingestion and chemical leaching, with strong evidence on bioaccumulation concerns."""
        },
        {
            "original_task": "Research solutions to mitigate microplastic pollution.",
            "critique_text": "Critique Skipped for Task: Research solutions to mitigate microplastic pollution.\nReason: Document content is empty or an error message from a previous step.\nDocument Content Provided: Error: Could not conduct research..."
        }
    ]

    print(f"Synthesising research for query: \"{sample_overall_query}\"")
    # This test will fail if no AI service is configured in the kernel above
    # synthesis_result = await synthesiser.synthesise_research(sample_overall_query, sample_critiqued_docs)
    # print(f"\nSynthesised Report:\n{synthesis_result}")

    # Test with all critiques skipped
    all_skipped_docs = [
        {
            "original_task": "Task A",
            "critique_text": "Critique Skipped for Task: Task A\nReason: Document content is empty..."
        },
        {
            "original_task": "Task B",
            "critique_text": "Critique Skipped for Task: Task B\nReason: Document content is empty..."
        }
    ]
    # print(f"\nSynthesising research for query (all skipped): \"{sample_overall_query}\"")
    # synthesis_all_skipped_result = await synthesiser.synthesise_research(sample_overall_query, all_skipped_docs)
    # print(f"\nSynthesised Report (all skipped):\n{synthesis_all_skipped_result}")

    print("\nNote: Synthesiser Agent tests are commented out. Uncomment and configure AI service to run.")

if __name__ == "__main__":
    # import asyncio
    # print("SynthesiserAgent class defined. To test, uncomment lines in _test_synthesiser_agent,")
    # print("ensure you have an OpenAI API key configured, and run this script directly.")
    # asyncio.run(_test_synthesiser_agent())
    pass 