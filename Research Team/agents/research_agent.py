import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
import os
import time
import sys

class ResearchAgent:
    def __init__(self, kernel: sk.Kernel, prompts_path: str, service_id: str | None = None):
        self.kernel = kernel
        self.service_id = service_id # Store the service_id for this agent
        self.direct_web_search = None  # To store reference to WebSearchPlugin if needed
        
        # Get the full path to the ConductResearch.prompty file
        research_prompt_file = os.path.join(prompts_path, "ResearchAgent", "ConductResearch.prompty")
        
        # Check if the file exists
        if not os.path.exists(research_prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {research_prompt_file}")
        
        # Load the prompt content from the file
        with open(research_prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Extract template from .prompty file
        template_start = prompt_content.find("template: |")
        template_format_start = prompt_content.find("template_format:")
        
        if template_start != -1 and template_format_start != -1:
            template_start += len("template: |")
            template = prompt_content[template_start:template_format_start].strip()
            
            # Create a function with the extracted template
            self.conduct_research_function = kernel.add_function(
                function_name="ConductResearch",
                plugin_name="ResearchAgent", 
                prompt=template,
                description="Synthesizes information from web search results"
            )
        else:
            raise ValueError("Could not extract template from the .prompty file")
            
        # Check if a global WebSearchPlugin instance is available
        try:
            # Get the module where main.py is defined
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, 'web_search_plugin_instance'):
                self.direct_web_search = main_module.web_search_plugin_instance
                print("📡 ResearchAgent using direct WebSearchPlugin instance.")
        except Exception as e:
            print(f"Note: No direct WebSearchPlugin available: {e}")

    async def perform_research_task(self, research_task_for_llm: str, search_query_for_web: str = None, additional_guidance: str = "") -> dict:
        """
        Perform a research task using web search.
        
        Args:
            research_task_for_llm: Description of the research task to be performed by the LLM.
            search_query_for_web: The query to use for web search. If None, research_task_for_llm will be used.
            additional_guidance: Optional additional guidance extracted from clarification questions.
            
        Returns:
            A dictionary containing:
                - text: The research results text
                - citations: List of citation sources
        """
        if not search_query_for_web:
            search_query_for_web = research_task_for_llm
        
        print(f"🔍 Performing web search for: '{search_query_for_web}'")
        print(f"📊 Researching with query: '{search_query_for_web}'...")
        
        web_search_results = {}
        search_success = False
        
        # Perform web search
        try:
            # Skip the failing kernel invoke method and directly use WebSearchPlugin if available
            if self.direct_web_search:
                print("🔍 Using direct WebSearchPlugin...")
                try:
                    direct_result = await self.direct_web_search.search(query=search_query_for_web, count=5)
                    
                    # Handle the new dictionary response format
                    if isinstance(direct_result, dict):
                        # Get text from either text_response or text field
                        text_content = direct_result.get("text_response", "") or direct_result.get("text", "")
                        
                        # Get citations from either formatted citations or annotations
                        citations_content = []
                        if "citations" in direct_result and direct_result["citations"]:
                            # Already formatted citations
                            citations_content = direct_result["citations"]
                        elif "annotations" in direct_result and direct_result["annotations"]:
                            # Convert annotations to citations
                            citations_content = self._convert_annotations_to_citations(direct_result["annotations"])
                        
                        web_search_results = {
                            "text": text_content,
                            "citations": citations_content
                        }
                        
                        if len(web_search_results["text"].strip()) > 50:
                            print(f"✅ Direct web search successful. Retrieved {len(web_search_results['text'])} characters with {len(web_search_results['citations'])} citations.")
                            search_success = True
                        # Handle raw response with results but no text fields (need to construct from results)
                        elif "results" in direct_result and direct_result["results"]:
                            search_results_text = "Search Results:\n\n"
                            citations = []
                            
                            # Process search results
                            for idx, result in enumerate(direct_result["results"], 1):
                                title = result.get("title", "Untitled")
                                url = result.get("url", "")
                                snippet = result.get("snippet", "No snippet available")
                                
                                search_results_text += f"[{idx}] {title}\nURL: {url}\n{snippet}\n\n"
                                
                                # Add to citations
                                citations.append({
                                    "title": title,
                                    "url": url
                                })
                            
                            web_search_results = {
                                "text": search_results_text,
                                "citations": citations
                            }
                            
                            if len(web_search_results["text"].strip()) > 50:
                                print(f"✅ Direct web search successful (constructed from results). Retrieved {len(direct_result['results'])} search results.")
                                search_success = True
                    # Handle string response (backward compatibility)
                    elif isinstance(direct_result, str) and len(direct_result.strip()) > 50:
                        web_search_results = {"text": str(direct_result), "citations": []}
                        print(f"✅ Direct web search successful (legacy string format). Retrieved {len(web_search_results['text'])} characters.")
                        search_success = True
                except Exception as e:
                    print(f"⚠️ Direct WebSearchPlugin failed: {e}")
            else:
                print("⚠️ No WebSearchPlugin available. Using general knowledge instead.")
            
            # If method failed, provide informative error
            if not search_success:
                print("⚠️ Web search methods unsuccessful. Using general knowledge instead.")
                web_search_results = {
                    "text": f"""Search for '{search_query_for_web}' did not return results. 
Please use your general knowledge to provide detailed information about this topic.
Focus specifically on addressing the research task: "{research_task_for_llm}".""",
                    "citations": []
                }
                search_success = True
        except Exception as e:
            print(f"❌ Error performing web search: {e}")
            web_search_results = {
                "text": f"Web search failed with error: {str(e)}",
                "citations": []
            }
        
        print(f"🧠 Analyzing search results...")
        
        # Ensure we have at least something for the LLM to work with
        if not search_success or len(web_search_results.get("text", "").strip()) < 50:
            web_search_results = {
                "text": f"""Search for '{search_query_for_web}' did not return sufficient results. 
Please use your general knowledge to provide detailed information about this topic.
Focus specifically on addressing the research task: "{research_task_for_llm}".""",
                "citations": []
            }
        
        # Prepare for synthesis
        print(f"📚 Synthesizing research from search results...")
        
        # Include additional guidance if provided
        guidance_section = ""
        if additional_guidance:
            guidance_section = f"\n\nAdditional Research Guidance:\n{additional_guidance}\n"
            print(f"💡 Including additional guidance in research synthesis.")
        
        # Add citations section to the search results
        citations_section = ""
        if web_search_results.get("citations"):
            citations_section = "\n\nSOURCES:\n"
            for i, citation in enumerate(web_search_results["citations"]):
                title = citation.get("title", "Untitled Source")
                url = citation.get("url", "No URL provided")
                citations_section += f"[{i+1}] {title}: {url}\n"
        
        synthesis_args = KernelArguments(
            research_task=research_task_for_llm,
            search_query=search_query_for_web,
            web_search_results=web_search_results["text"] + guidance_section + citations_section
        )
        
        try:
            print("🔄 Performing deep research synthesis...")
            synthesis_result = await self.kernel.invoke(
                self.conduct_research_function,
                synthesis_args,
                # Pass the specific service_id if available, else SK uses the default
                service_id=self.service_id 
            )
            
            print(f"✅ Research synthesis complete.")
            
            result_text = ""
            if hasattr(synthesis_result, 'value'):
                result_text = str(synthesis_result.value).strip()
            else:
                result_text = str(synthesis_result).strip()
            
            # Add a direct reminder to include citations in the report if they exist
            if web_search_results.get("citations") and len(web_search_results["citations"]) > 0:
                print(f"📝 Found {len(web_search_results['citations'])} citations to include in the report")
            
            # Return the result with citations
            return {
                "text": result_text,
                "citations": web_search_results.get("citations", [])
            }
        except Exception as e:
            print(f"❌ ResearchAgent: Error invoking synthesis function for task '{research_task_for_llm}': {e}")
            return {
                "text": f"Error: Could not conduct research synthesis for task: {research_task_for_llm}. Details: {str(e)}",
                "citations": []
            }
    
    def _convert_annotations_to_citations(self, annotations):
        """
        Convert annotations from the OpenAI response to citation format.
        
        Args:
            annotations: List of annotation objects
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        unique_urls = set()
        
        for annotation in annotations:
            url = annotation.get("url", "")
            # Remove tracking parameters for cleaner URLs
            clean_url = url.split("?utm_source=")[0] if "?utm_source=" in url else url
            
            if clean_url and clean_url not in unique_urls:
                unique_urls.add(clean_url)
                citations.append({
                    "title": annotation.get("title", "Source"),
                    "url": clean_url
                })
        
        return citations

# Example usage (for testing)
async def _test_researcher_with_web():
    kernel = sk.Kernel()
    
    # Add a WebSearchPlugin instance
    try:
        from tools.web_tools import WebSearchPlugin 
        kernel.add_plugin(WebSearchPlugin(), plugin_name="WebSearch")
        print("🛠️ WebSearchPlugin registered for test.")
    except ImportError:
        print("❌ Could not import WebSearchPlugin. Make sure tools/web_tools.py exists and is in PYTHONPATH.")
        return

    # Path to prompts
    prompts_root_dir = "../prompts" 
    try:
        researcher = ResearchAgent(kernel, prompts_root_dir)
    except Exception as e:
        print(f"Error initializing ResearchAgent: {e}. This might be due to prompty files not found at {prompts_root_dir}/ResearchAgent")
        return
    
    task1 = "What are the latest breakthroughs in perovskite solar cell efficiency in 2023?"
    print(f"\n🔬 Performing research task (with web search): \"{task1}\"")
    
    result = await researcher.perform_research_task(task1)
    print(f"\n🧪 Research result: {result['text'][:200]}...")
    print(f"\n📚 Citations ({len(result['citations'])}): ")
    for i, citation in enumerate(result['citations']):
        print(f" - [{i+1}] {citation.get('title', 'Untitled')}: {citation.get('url', 'No URL')}")
    
    print("\nNote: To run a full test with this ResearchAgent:")
    print("  1. Ensure tools.web_tools.WebSearchPlugin is available and works.")
    print("  2. Configure your AI service in main.py.")
    print("  3. Ensure your OPENAI_API_KEY is set as an environment variable.")

if __name__ == "__main__":
    # import asyncio
    # print("ResearchAgent class defined. To test with web search:")
    # asyncio.run(_test_researcher_with_web())
    pass 