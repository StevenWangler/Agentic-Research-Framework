import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions import KernelFunctionFromPrompt
import os
import re

class PlannerAgent:
    def __init__(self, kernel: sk.Kernel, prompts_path: str, service_id: str | None = None):
        self.kernel = kernel
        self.service_id = service_id
        
        # Get the full path to the Plan.prompty file
        planner_prompt_file = os.path.join(prompts_path, "PlannerAgent", "Plan.prompty")
        
        # Check if the file exists
        if not os.path.exists(planner_prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {planner_prompt_file}")
        
        # Load the prompt content from the file
        with open(planner_prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Extract template from .prompty file (basic approach)
        # This is a simple extraction - not a full parser for .prompty files
        # Find the template section between template: and template_format:
        template_start = prompt_content.find("template: |")
        template_format_start = prompt_content.find("template_format:")
        
        if template_start != -1 and template_format_start != -1:
            template_start += len("template: |")
            template = prompt_content[template_start:template_format_start].strip()
            
            # Create a function with the extracted template
            self.plan_function = kernel.add_function(
                function_name="Plan",
                plugin_name="PlannerAgent", 
                prompt=template,
                description="Generates a research plan based on the user's query"
            )
        else:
            raise ValueError("Could not extract template from the .prompty file")

    async def generate_plan(self, query: str) -> str:
        arguments = KernelArguments(query=query)
        try:
            result = await self.kernel.invoke(
                self.plan_function,
                arguments,
                service_id=self.service_id
            )
            return str(result)
        except Exception as e:
            # Handle cases where the AI model might not be configured or other errors
            print(f"Error invoking planner function: {e}")
            return "Error: Could not generate plan."
    
    def extract_research_tasks_from_plan(self, plan_text: str) -> list:
        """
        Extract research tasks from the research plan.
        
        Args:
            plan_text: The research plan text
            
        Returns:
            list: List of research tasks
        """
        if not plan_text or plan_text.startswith("Error:"):
            print("Cannot extract research tasks from an empty or error plan.")
            return []
        
        research_tasks = []
        plan_lines = plan_text.strip().split('\n')
        
        for line in plan_lines:
            line = line.strip()
            if "[ResearchAgent]" in line:
                # Parse the research task
                search_query = None
                task_description = line  # Default
                
                # Look for explicit search queries
                specific_search_pattern = r"\s*\d*\.\s*\[ResearchAgent\]\s*Search for:\s*['\"](?P<query>.*?)['\"]"
                specific_search_match = re.search(specific_search_pattern, line, re.IGNORECASE)
                
                general_task_pattern = r"\s*\d*\.\s*\[ResearchAgent\]\s*(?P<task>.*)"
                general_task_match = re.search(general_task_pattern, line, re.IGNORECASE)
                
                if specific_search_match:
                    # Extract the specific search query
                    search_query = specific_search_match.group("query").strip()
                    task_description = search_query
                    print(f"📝 Found specific research task: '{search_query}'")
                elif general_task_match:
                    # Extract the task description
                    task_desc = general_task_match.group("task").strip()
                    
                    # Check if there's a search query embedded in the task
                    inner_search_match = re.match(r"Search for:\s*['\"](?P<query>.*?)['\"]", task_desc, re.IGNORECASE)
                    if inner_search_match:
                        search_query = inner_search_match.group("query").strip()
                        task_description = search_query
                        print(f"📝 Extracted research task: '{search_query}'")
                    else:
                        task_description = task_desc
                        print(f"📝 Using general task as research task: '{task_desc}'")
                
                if task_description:
                    research_tasks.append(task_description)
        
        print(f"📋 Extracted {len(research_tasks)} research tasks from the plan.")
        return research_tasks

# Example usage (for testing, will be moved to main.py later)
async def _test_planner():
    kernel = sk.Kernel()
    
    # IMPORTANT: Configure your AI service connector here
    # Example for OpenAI:
    # from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
    # api_key = "YOUR_OPENAI_API_KEY"  # Replace with your actual key
    # org_id = "YOUR_OPENAI_ORG_ID"    # Replace if you have one
    # service_id = "default_chat"
    # try:
    #     kernel.add_service(
    #         OpenAIChatCompletion(
    #             service_id=service_id,
    #             ai_model_id="gpt-3.5-turbo", # Or your preferred model
    #             api_key=api_key,
    #             org_id=org_id
    #         )
    #     )
    # except Exception as e:
    #     print(f"Error adding AI service: {e}")
    #     print("Please ensure your OpenAI API key and organization ID (if applicable) are correctly set.")
    #     print("Skipping planner test.")
    #     return

    # Assuming your script is in deep_research_agent/agents/ and prompts are in deep_research_agent/prompts/
    # The path to the root of prompts directory from here would be "../prompts"
    prompts_root_dir = "../prompts" 

    # Check if a service is available
    # if not kernel.get_service(service_id):
    #     print(f"AI service '{service_id}' not found. Skipping planner test.")
    #     print("Please configure an AI service (e.g., OpenAI) in the kernel above.")
    #     return

    # When testing, provide the service_id if it's expected by the constructor
    planner = PlannerAgent(kernel, prompts_root_dir) # Add service_id here if testing with specific service
    
    user_query = "What are the latest advancements in AI for drug discovery?"
    print(f"Generating plan for query: '{user_query}'...")
    
    plan = await planner.generate_plan(user_query)
    print(f"\nGenerated Plan:\n{plan}")
    
    # Test extraction of research tasks
    research_tasks = planner.extract_research_tasks_from_plan(plan)
    print("\nExtracted Research Tasks:")
    for i, task in enumerate(research_tasks):
        print(f"{i+1}. {task}")

if __name__ == "__main__":
    # import asyncio
    # print("PlannerAgent class defined. To test, uncomment the lines below,")
    # print("ensure you have an OpenAI API key, and run this script directly.")
    # print("You might need to install openai and semantic-kernel: pip install semantic-kernel openai")
    # print("Make sure to configure your API key in the _test_planner function.")
    # asyncio.run(_test_planner())
    pass 