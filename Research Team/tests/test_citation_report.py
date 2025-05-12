#!/usr/bin/env python3
"""
Test script to verify citation handling in the research pipeline.
This script tests only the components needed to verify citation handling.
"""

import asyncio
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import semantic_kernel as sk
from tools.web_tools import WebSearchPlugin
from agents.research_agent import ResearchAgent
from orchestrator.research_orchestrator import ResearchOrchestrator

# Load environment variables
load_dotenv()

class MockUI:
    """Simple mock UI for testing"""
    def display_research_start(self, task):
        print(f"\n🔬 Starting research on: {task}")
    
    def display_research_result(self, task, result):
        print(f"✅ Research completed for: {task[:50]}...")
        print(f"Result length: {len(result)} characters")
    
    def display_critique_start(self, task):
        print(f"\n🧐 Starting critique for: {task[:50]}...")
    
    def display_critique_result(self, critique):
        print(f"✅ Critique completed, {len(critique)} characters")
    
    def display_synthesis_start(self):
        print("\n🔄 Starting synthesis...")
    
    def display_synthesis_stats(self, report):
        print(f"✅ Synthesis completed, {len(report)} characters")
        
        # Check if the report contains citations
        if "## Sources and Citations" in report:
            citation_section = report.split("## Sources and Citations")[1].strip()
            citation_count = citation_section.count("](http")
            print(f"📚 Report includes {citation_count} citations")
            
            # Add more detailed output for debugging
            print("\n--- SYNTHESIS CITATIONS SECTION PREVIEW ---")
            print(citation_section[:500] + ("..." if len(citation_section) > 500 else ""))
            print("--- END SYNTHESIS CITATIONS PREVIEW ---\n")
        else:
            print("⚠️ No citations section found in the synthesis report")
    
    def display_final_report(self, report):
        print("\n📑 Final report completed")
        
        # Check if the report contains citations
        if "## Sources and Citations" in report:
            citation_section = report.split("## Sources and Citations")[1].strip()
            citation_count = citation_section.count("](http")
            print(f"📚 Final report includes {citation_count} citations")
            
            # Print the citations section
            print("\n--- FINAL REPORT CITATIONS SECTION ---")
            print(citation_section[:1000] + ("..." if len(citation_section) > 1000 else ""))
            print("--- END CITATIONS ---\n")
        else:
            # Check other common citation section headers
            for section_title in ["## References", "## Sources", "## Bibliography"]:
                if section_title in report:
                    citation_section = report.split(section_title)[1].strip()
                    citation_count = citation_section.count("](http")
                    print(f"📚 Final report includes {citation_count} citations under '{section_title}'")
                    
                    # Print the citations section
                    print(f"\n--- FINAL REPORT {section_title.strip('#')} SECTION ---")
                    print(citation_section[:1000] + ("..." if len(citation_section) > 1000 else ""))
                    print("--- END CITATIONS ---\n")
                    break
            else:
                print("⚠️ No citations section found in the final report with any known header")
                
                # Last resort: check for any markdown links that might be citations
                link_pattern = r'\[(.*?)\]\((https?://.*?)\)'
                import re
                links = re.findall(link_pattern, report)
                if links:
                    print(f"🔍 Found {len(links)} markdown links in the report that might be citations:")
                    for i, (text, url) in enumerate(links[:5]):
                        print(f"  {i+1}. [{text}]({url})")
                    if len(links) > 5:
                        print(f"  ... and {len(links) - 5} more")
    
    def display_file_save_result(self, file_paths):
        print(f"📁 Report saved to: {file_paths}")
    
    def get_clarification_responses(self, questions):
        return ""
    
    def display_clarification_status(self, has_clarifications):
        pass
    
    def display_clarification_insights(self, insights):
        pass
    
    def display_plan(self, plan):
        pass
    
    def get_initial_query(self):
        return "Test query"

class MockConfigManager:
    """Simple configuration manager for testing"""
    def __init__(self):
        self.prompts_path = "prompts"
        self.reports_dir = "reports"
    
    def setup_kernel_services(self, kernel):
        return {
            "PlannerAgent": None,
            "ClarifierAgent": None,
            "ResearchAgent": None,
            "CritiqueAgent": None,
            "SynthesiserAgent": None,
            "WriterAgent": None
        }

async def test_research_with_citations():
    """Test the research pipeline with a focus on citations"""
    kernel = sk.Kernel()
    
    # Create a WebSearchPlugin instance
    web_search_plugin = WebSearchPlugin()
    
    try:
        # Add the plugin to the kernel - use the appropriate method based on SK version
        if hasattr(kernel, 'import_native_plugin_from_object'):
            kernel.import_native_plugin_from_object(web_search_plugin, "WebSearch")
        elif hasattr(kernel, 'add_plugin'):
            kernel.add_plugin(web_search_plugin, "WebSearch")
        else:
            print("⚠️ Unable to determine correct method to register plugin, trying direct way")
            # Skip registration and proceed with direct access
        
        print("✅ WebSearchPlugin registered successfully")
    except Exception as e:
        print(f"⚠️ Error registering WebSearchPlugin: {e}")
        print("Continuing with direct WebSearchPlugin access")
    
    # Set up a global instance for direct access by the ResearchAgent
    sys.modules["__main__"].web_search_plugin_instance = web_search_plugin
    
    # Just test the WebSearchPlugin directly first
    web_search_output = await test_web_search_only(web_search_plugin)
    
    # Create a research agent
    try:
        researcher = ResearchAgent(kernel, "prompts")
        print("✅ ResearchAgent created (note: using default prompts path)")
    except FileNotFoundError:
        print("⚠️ Prompt files not found. Skipping ResearchAgent test.")
        return
    
    # Run a research task
    research_query = "What are the latest advancements in AI for drug discovery?"
    
    print(f"\n🔍 Performing research for: '{research_query}'")
    result = await researcher.perform_research_task(research_query)
    
    # Check if citations are included
    citation_count = len(result.get("citations", []))
    print(f"\n📚 Research result includes {citation_count} citations")
    
    if citation_count > 0:
        print("\nCitation examples:")
        for i, citation in enumerate(result["citations"][:3]):
            print(f"{i+1}. {citation.get('title', 'Untitled')}: {citation.get('url', 'No URL')}")
        
        if citation_count > 3:
            print(f"... and {citation_count-3} more")
    else:
        # If no citations in the researcher result, but we had them in the web search,
        # we need to debug why they were lost
        if web_search_output and len(web_search_output.get("citations", [])) > 0:
            print("⚠️ Citations were found in web search but lost in research agent results")
            print("This indicates a problem in citation handling in the ResearchAgent")
    
    # If we got this far, try the full orchestrator
    try:
        print("\n🚀 Testing full orchestrator pipeline...")
        mock_ui = MockUI()
        mock_config = MockConfigManager()
        
        orchestrator = ResearchOrchestrator(mock_config, kernel, mock_ui)
        
        # Use just the research phase and synthesis since that's where we need to test citations
        critiqued_documents = [{
            "task": research_query,
            "original": result.get("text", ""),
            "critique": result.get("text", ""),
            "citations": result.get("citations", [])
        }]
        
        print(f"\n📋 Ready to test synthesis with {len(critiqued_documents[0]['citations'])} citations")
        
        # Test synthesis phase which should include citations
        synthesis_result = await orchestrator._handle_synthesis_phase(research_query, critiqued_documents)
        
        # Check if citations are included in synthesis
        if "## Sources and Citations" in synthesis_result:
            print("✅ Citations successfully included in the synthesized report")
            
            # Now test the writer phase to see if citations are preserved
            print("\n✍️ Testing writer phase...")
            final_report = await orchestrator._handle_writing_phase(research_query, synthesis_result)
            
            # Check if citations are in the final report
            if "## Sources and Citations" in final_report:
                print("✅ Citations successfully preserved in the final formatted report")
            else:
                for section_title in ["## References", "## Sources", "## Bibliography"]:
                    if section_title in final_report:
                        print(f"✅ Citations included in final report under '{section_title}' section")
                        break
                else:
                    print("❌ Citations section was LOST in the final report formatting!")
                    print("→ This indicates a problem in the WriterAgent citation handling")
                    
                    # Save samples for deeper debugging
                    print("\nSaving samples for debugging:")
                    with open("debug_synthesis_result.md", "w") as f:
                        f.write(synthesis_result)
                    with open("debug_final_report.md", "w") as f:
                        f.write(final_report)
                    print("✅ Debug samples saved to debug_synthesis_result.md and debug_final_report.md")
        else:
            print("❌ No citations section in the synthesized report")
    
    except Exception as e:
        print(f"❌ Error in orchestrator test: {e}")

async def test_web_search_only(plugin=None):
    """Fallback test method just for WebSearchPlugin and citation extraction"""
    if plugin is None:
        plugin = WebSearchPlugin()
    
    query = "What are the latest advancements in AI for drug discovery?"
    
    print(f"\n🔎 Testing WebSearchPlugin directly with: '{query}'")
    try:
        output = await plugin.search(query)
        
        # Check citations
        citation_count = len(output.get("citations", []))
        print(f"\n📚 Search result includes {citation_count} citations")
        
        if citation_count > 0:
            print("\nCitation examples:")
            for i, citation in enumerate(output["citations"][:3]):
                print(f"{i+1}. {citation.get('title', 'Untitled')}: {citation.get('url', 'No URL')}")
            
            if citation_count > 3:
                print(f"... and {citation_count-3} more")
        
        # Print text response preview
        if output.get("text_response"):
            print(f"\n📝 Text Response preview:\n{output['text_response'][:200]}...\n")
        
        # Print annotations if available for debugging
        if output.get("annotations"):
            print(f"\n🔍 Raw annotations from API response:")
            for i, annotation in enumerate(output["annotations"][:2]):
                print(f"{i+1}. {annotation.get('title', 'Untitled')}: {annotation.get('url', 'No URL')}")
            
            if len(output["annotations"]) > 2:
                print(f"... and {len(output['annotations'])-2} more")
        
        return output
    
    except Exception as e:
        print(f"❌ Error in WebSearchPlugin test: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Starting citation handling test...")
    asyncio.run(test_research_with_citations())
    print("✅ Test completed") 