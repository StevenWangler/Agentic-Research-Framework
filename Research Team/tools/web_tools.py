import os
import asyncio
import time
from typing import Optional, List, Dict, Any, Tuple
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class WebSearchPlugin:
    """
    A plugin that performs real web searching using OpenAI's web_search tool,
    returning results with titles, URLs, and snippets.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4.1",
        default_count: int = 5,
        temperature: float = 0.0,
        max_tokens: int = 4096,  # Keep for compatibility but won't be used
        simulate_delay: bool = False
    ):
        """
        Initialize the WebSearchPlugin.

        Args:
            api_key: OpenAI API key. If None, will load from OPENAI_API_KEY env var.
            model: The OpenAI model to use for web search (Responses API).
            default_count: Default number of search results to retrieve.
            temperature: Temperature for the model (between 0 and 1).
            max_tokens: Maximum tokens to generate in response (stored but not used with Responses API).
            simulate_delay: Whether to simulate a delay for testing purposes.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.default_count = default_count
        self.temperature = temperature
        self.max_tokens = max_tokens  # Stored but not used with Responses API
        self.simulate_delay = simulate_delay

    async def search(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform a real web search for the given query and return structured results.

        Args:
            query: The search query string.
            count: Number of results to return (max). Defaults to default_count.

        Returns:
            A dict with:
                - results: List of dicts containing 'title', 'url', and 'snippet'.
                - response: The full response object from the API.
                - text_response: The extracted text response from the model.
                - annotations: List of URL citations with metadata.
                - text: Formatted text response for backward compatibility
                - citations: Formatted citations for the report
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        if count is None:
            count = self.default_count

        print(f"🔍 Searching the web for: '{query}'")
        
        # Simulate delay if configured (for testing)
        if self.simulate_delay:
            delay = 1.5  # seconds
            print(f"⏳ Simulating search delay of {delay} seconds...")
            await asyncio.sleep(delay)
        
        # Call the Responses API with the built-in web_search tool
        start_time = time.time()
        response = self.client.responses.create(
            model=self.model,
            temperature=self.temperature,
            # Note: max_tokens is not used here as it's not supported by the Responses API
            input=query,
            tools=[{"type": "web_search"}]
        )
        search_time = time.time() - start_time
        
        print(f"✅ Search completed in {search_time:.2f} seconds")

        # Extract structured search results from web search tool call
        tool_responses = getattr(response, "tool_responses", {})
        search_data = tool_responses.get("web_search", {})
        raw_results = search_data.get("results", [])

        # Normalize into a consistent list of dicts
        results: List[Dict[str, Any]] = []
        for item in raw_results:
            results.append({
                "title": item.get("title", "").strip(),
                "url": item.get("url", "").strip(),
                "snippet": item.get("snippet", "").strip()
            })
            
        # Extract text response and annotations from the new response format
        text_response, annotations = self._extract_text_and_annotations(response)
        
        # Create properly formatted citations for the report system
        citations = self._format_citations_for_report(annotations)
        
        num_results = len(results)
        num_citations = len(citations)
        print(f"📊 Found {num_results} search results and {num_citations} citations")
        
        return {
            "results": results, 
            "response": response,
            "text_response": text_response,
            "annotations": annotations,
            # Add backward compatibility fields
            "text": text_response,  # For compatibility with older code
            "citations": citations  # Properly formatted citations for the report
        }
        
    def _extract_text_and_annotations(self, response) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract the text response and annotations from the new response format.
        
        Args:
            response: The full response object from the API.
            
        Returns:
            Tuple containing:
                - text_response: The extracted text response
                - annotations: List of URL citation annotations
        """
        text_response = ""
        annotations = []
        
        # Navigate through the output structure to find text and annotations
        if hasattr(response, "output") and response.output:
            for output_item in response.output:
                # Look for message type outputs that contain content
                if hasattr(output_item, "type") and output_item.type == "message":
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            # Extract text content
                            if hasattr(content_item, "type") and content_item.type == "output_text":
                                text_response = getattr(content_item, "text", "")
                                
                                # Extract annotations if present
                                content_annotations = getattr(content_item, "annotations", [])
                                for annotation in content_annotations:
                                    if hasattr(annotation, "type") and annotation.type == "url_citation":
                                        annotations.append({
                                            "type": "url_citation",
                                            "title": getattr(annotation, "title", ""),
                                            "url": getattr(annotation, "url", ""),
                                            "start_index": getattr(annotation, "start_index", 0),
                                            "end_index": getattr(annotation, "end_index", 0)
                                        })
        
        return text_response, annotations
    
    def _format_citations_for_report(self, annotations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format annotations as citations for the final report.
        
        Args:
            annotations: List of URL citation annotations
            
        Returns:
            List of citations in the format expected by the report generation system
        """
        # Create a dict to deduplicate citations by URL
        unique_citations = {}
        
        for annotation in annotations:
            url = annotation.get("url", "")
            # Remove tracking parameters from URLs for better deduplication
            clean_url = url.split("?utm_source=")[0] if "?utm_source=" in url else url
            
            if clean_url and clean_url not in unique_citations:
                unique_citations[clean_url] = {
                    "title": annotation.get("title", "Untitled Source"),
                    "url": clean_url
                }
        
        # Convert back to a list
        return list(unique_citations.values())


# Example usage for direct testing
async def _test_search():
    plugin = WebSearchPlugin()
    queries = [
        "latest advancements in AI-driven drug discovery",
        "Why do we only see one side of the moon",
        "Do you think the Red Wings will be good in 2025-2026?"
    ]

    for q in queries:
        print(f"\n🔎 Searching for: {q}")
        try:
            output = await plugin.search(q, count=3)
            # Print full response object
            print(f"Full response:\n{output['response']}\n")
            
            # Print text response if available
            if output["text_response"]:
                print(f"📝 Text Response:\n{output['text_response'][:300]}...\n")
            
            # Print formatted citations if available
            if output["citations"]:
                print(f"📚 Formatted Citations for Report:")
                for idx, citation in enumerate(output["citations"], start=1):
                    print(f"  {idx}. {citation['title']} ({citation['url']})")
                print()
            
            # Print annotations if available
            if output["annotations"]:
                print(f"🔗 Raw URL Citations:")
                for idx, anno in enumerate(output["annotations"], start=1):
                    print(f"  {idx}. {anno['title']} ({anno['url']})")
                print()
            
            # Print search results
            print("🌐 Search Results:")
            for idx, res in enumerate(output["results"], start=1):
                print(f"{idx}. {res['title']} ({res['url']})")
                print(f"   {res['snippet'][:150]}...\n")
        except Exception as e:
            print(f"❌ Error searching '{q}': {e}")

if __name__ == "__main__":
    asyncio.run(_test_search())