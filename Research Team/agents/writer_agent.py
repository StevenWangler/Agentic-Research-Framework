import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
import os
import re
import json

class WriterAgent:
    def __init__(self, kernel: sk.Kernel, prompts_path: str, service_id: str | None = None):
        self.kernel = kernel
        self.service_id = service_id
        
        # Get the full path to the FormatReportMarkdown.prompty file
        writer_prompt_file = os.path.join(prompts_path, "WriterAgent", "FormatReportMarkdown.prompty")
        
        # Check if the file exists
        if not os.path.exists(writer_prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {writer_prompt_file}")
        
        # Load the prompt content from the file
        with open(writer_prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Extract template from .prompty file
        template_start = prompt_content.find("template: |")
        template_format_start = prompt_content.find("template_format:")
        
        if template_start != -1 and template_format_start != -1:
            template_start += len("template: |")
            template = prompt_content[template_start:template_format_start].strip()
            
            # Create a function with the extracted template
            self.format_report_markdown_function = kernel.add_function(
                function_name="FormatReportMarkdown",
                plugin_name="WriterAgent", 
                prompt=template,
                description="Formats synthesized research text into a well-structured Markdown report"
            )
        else:
            raise ValueError("Could not extract template from the .prompty file")

    async def format_report_as_markdown(self, user_query: str, synthesized_report_text: str) -> str:
        """
        Formats the synthesized report text into Markdown.
        """
        if not synthesized_report_text:
            # If the input is completely empty, we still want to generate a note about it.
            # The prompt itself handles error strings like "Error: ..."
            synthesized_report_text = "Notice: No content was provided for the synthesized report. The research process may have encountered an issue or yielded no information."

        # Preserve the Sources and Citations section if it exists
        citations_section = ""
        if "## Sources and Citations" in synthesized_report_text:
            report_parts = synthesized_report_text.split("## Sources and Citations")
            synthesized_report_text = report_parts[0].strip()
            if len(report_parts) > 1:
                citations_section = "## Sources and Citations" + report_parts[1]
                print(f"📚 Found citations section in synthesized report: {len(citations_section)} characters")

        arguments = KernelArguments(
            user_query=user_query,
            synthesized_report_text=synthesized_report_text
        )
        
        try:
            result = await self.kernel.invoke(
                self.format_report_markdown_function,
                arguments,
                service_id=self.service_id
            )
            
            # Extract pure text content, handling different possible result types
            result_text = ""
            if hasattr(result, 'value'): 
                result_text = str(result.value).strip()
            else:
                result_text = str(result).strip()
            
            # Clean up JSON formatting if present
            clean_text = self._clean_json_format(result_text)
            
            # Append the citations section back to the formatted report
            if citations_section:
                # Check if the report already has a references/sources/bibliography section
                # and remove it to prevent duplication
                reference_sections = ["## References", "## Sources", "## Bibliography", "## Sources and Citations"]
                
                # Find if any reference section exists and remove it
                for section in reference_sections:
                    if section in clean_text:
                        parts = clean_text.split(section)
                        clean_text = parts[0].strip()
                        # Only remove the first occurrence
                        break
                        
                # Add the citations at the end with spacing
                clean_text += "\n\n" + citations_section
                print(f"✅ Added citations section to final report")
            else:
                print("⚠️ No citations section found to append to the report")
            
            return clean_text
            
        except Exception as e:
            error_message = f"Error invoking writer function: {e}. Query: {user_query}"
            print(error_message)
            # Fallback: return the raw text with an error prefix if formatting fails
            formatted_text = f"# Report for: {user_query}\n\n## Error During Report Formatting\n\nAn error occurred while formatting the report: {str(e)}\n\n**Raw Synthesized Text (if available):**\n```\n{synthesized_report_text}\n```"
            
            # Still include citations if available
            if citations_section:
                formatted_text += "\n\n" + citations_section
            
            return formatted_text

    def _clean_json_format(self, text: str) -> str:
        """
        Clean up JSON formatting in text to return pure markdown.
        This handles cases where the output might contain nested JSON objects or other formatting artifacts.
        """
        # First, try to see if the entire string is valid JSON
        if text.strip().startswith('{') and text.strip().endswith('}'):
            try:
                json_obj = json.loads(text)
                # If it's a dictionary with 'content', extract that
                if isinstance(json_obj, dict) and 'content' in json_obj:
                    return json_obj['content']
                # Try to find markdown content in any common JSON keys
                for key in ['markdown', 'text', 'output', 'result', 'message']:
                    if key in json_obj:
                        return json_obj[key]
            except json.JSONDecodeError:
                pass  # Not valid JSON, continue with other cleaning methods
        
        # Look for ChatCompletionMessage format in the string
        completion_pattern = r'ChatCompletionMessage\(content=["\'](.*?)["\']\,'
        match = re.search(completion_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
            
        # Check for markdown content between triple backticks
        markdown_block = re.search(r'```markdown\s*(.*?)\s*```', text, re.DOTALL)
        if markdown_block:
            return markdown_block.group(1)
            
        # If we can't extract clean content using the above methods, 
        # just return the original but strip ChatGPT response prefixes
        cleaned = re.sub(r'^(Here is|I\'ve formatted|The following is|Here\'s).*?:\s*', '', text, flags=re.IGNORECASE)
        
        return cleaned

# Example usage (for testing)
async def _test_writer_agent():
    kernel = sk.Kernel()
    # Configure AI service (e.g., OpenAI)
    # from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
    # import os
    # api_key = os.getenv("OPENAI_API_KEY")
    # org_id = os.getenv("OPENAI_ORG_ID")
    # service_id = "default_chat" 
    # if not api_key:
    #     print("OpenAI API key not found. Set OPENAI_API_KEY. Skipping writer test.")
    #     return
    # try:
    #     kernel.add_service(
    #         OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    #     )
    # except Exception as e:
    #     print(f"Error adding AI service for testing: {e}. Skipping writer test.")
    #     return
    # if not kernel.get_service(service_id):
    #     print(f"AI service '{service_id}' not configured. Skipping writer agent test.")
    #     return

    prompts_root_dir = "../prompts"
    # When testing, provide the service_id if it's expected by the constructor
    writer = WriterAgent(kernel, prompts_root_dir) # Add service_id here if testing

    sample_query = "The Future of Renewable Energy"
    sample_synthesized_report = """
Introduction: Renewable energy is pivotal for a sustainable future. This report covers key aspects.
Key Findings:
1. Solar power capacity has grown exponentially.
2. Wind energy is becoming increasingly cost-competitive.
3. Challenges remain in energy storage and grid integration.
Conclusion: The transition to renewable energy is accelerating, driven by technological advancements and policy support, despite some hurdles.
    """

    print(f"Formatting report for query: \"{sample_query}\"")
    # This test will fail if no AI service is configured
    # formatted_report = await writer.format_report_as_markdown(sample_query, sample_synthesized_report)
    # print(f"\nFormatted Markdown Report:\n{formatted_report}")

    error_report_text = "Error: Synthesis failed due to missing critical data."
    # print(f"\nFormatting error report for query: \"{sample_query}\"")
    # formatted_error_report = await writer.format_report_as_markdown(sample_query, error_report_text)
    # print(f"\nFormatted Error Report:\n{formatted_error_report}")
    
    empty_report_text = ""
    # print(f"\nFormatting empty report for query: \"{sample_query}\"")
    # formatted_empty_report = await writer.format_report_as_markdown(sample_query, empty_report_text)
    # print(f"\nFormatted Empty Report:\n{formatted_empty_report}")

    print("\nNote: Writer Agent tests are commented out. Uncomment and configure AI service to run.")


if __name__ == "__main__":
    # import asyncio
    # print("WriterAgent class defined. To test, uncomment lines in _test_writer_agent,")
    # print("ensure you have an OpenAI API key configured, and run this script directly.")
    # asyncio.run(_test_writer_agent())
    pass 