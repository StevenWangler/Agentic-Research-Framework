import sys
from utils.text_utils import display_clean_report

class ConsoleInterface:
    def __init__(self):
        """Initialize the console interface"""
        pass
        
    def get_initial_query(self):
        """Get the initial research query from the user"""
        print("\n🔍 Enter your research query: ", end="")
        query = input().strip()
        
        if not query:
            print("No query entered. Exiting.")
            sys.exit(0)
            
        return query
    
    def get_clarification_responses(self, clarifying_questions):
        """Get user responses to clarifying questions"""
        print("\n❓ Please answer these clarifying questions to improve your research results:")
        print(clarifying_questions)
        print("\nPlease provide your answers to these questions (or press Enter to skip):")
        responses = input("> ").strip()
        
        return responses
    
    def display_clarification_status(self, has_clarifications):
        """Display status message about clarifications"""
        if has_clarifications:
            print(f"\n✅ Thank you for the clarifications. Proceeding with enhanced query.")
        else:
            print(f"\n✅ Proceeding with the original query.")
    
    def display_plan(self, plan):
        """Display the research plan"""
        print("\n📝 Research Plan:")
        print(plan)
    
    def display_clarification_insights(self, insights):
        """Display extracted insights from clarification questions"""
        if insights:
            print(f"\n💡 Extracted guidance from clarification questions:\n{insights}")
    
    def display_research_start(self, task):
        """Display information about starting a research task"""
        print(f"\n🔬 Starting research on task: \"{task}\"")
    
    def display_research_task_start(self, task_description, search_query):
        """Display information about starting a research task"""
        print(f"\n🔬 ResearchAgent: LLM Task=\"{task_description}\", Web Query=\"{search_query}\"")
    
    def display_research_result(self, task, result):
        """Display the result of a research task"""
        if isinstance(result, str) and result.startswith("Error:"):
            print(f"⚠️ Research task (LLM: '{task}') failed: {result}")
        else:
            print(f"📄 Result snippet (LLM: '{task}'):\n{result[:200].strip()}...")
    
    def display_critique_start(self, task):
        """Display information about starting document critique"""
        print(f"\n⚖️ Critiquing document for task: \"{task}\"")
    
    def display_critique_result(self, critique):
        """Display the result of document critique"""
        print(f"📋 Critique Snippet:\n{critique[:300].strip()}...")
    
    def display_synthesis_start(self):
        """Display information about starting synthesis"""
        print("\n🧠 Starting Deep Synthesis Phase...")
        print("⏳ The model will spend 10-20 minutes creating a comprehensive academic-quality research paper...")
        print("⏳ This extended processing time allows for deep analysis and truly thorough research...")
        print("⏳ The focus is on creating a seriously in-depth, accurate, and informative research report...")
    
    def display_synthesis_stats(self, report):
        """Display statistics about the synthesized report"""
        report_word_count = len(report.split())
        print("\n📜 Comprehensive Research Paper Generated")
        print(f"📊 Report statistics:")
        print(f"   - Approximately {report_word_count} words")
        print(f"   - {len(report)} characters")
        print(f"   - Academic-quality, in-depth research paper format")
        print(f"\nSnippet from introduction:\n{report[:300].strip()}...")
    
    def display_final_report(self, report):
        """Display information about the final report without printing its full content"""
        report_word_count = len(report.split())
        print("\n📜 Final In-Depth Research Report Generated")
        print(f"📊 Report statistics:")
        print(f"   - Approximately {report_word_count} words")
        print(f"   - {len(report)} characters")
        print(f"   - Professional academic-quality comprehensive research paper")
        
        # Check if report contains citations section
        if "## Sources and Citations" in report:
            citation_section = report.split("## Sources and Citations")[1].strip()
            citation_count = citation_section.count("\n") + 1
            print(f"   - {citation_count} citations included")
        
        # Provide information about the depth
        if report_word_count > 5000:
            print(f"   - Extensive depth ({report_word_count} words) - a truly comprehensive analysis")
        elif report_word_count > 3000:
            print(f"   - Good depth ({report_word_count} words) - a thorough analysis")
        
        print(f"\nSnippet from beginning:\n{report[:200].strip()}...")
        print("\n(Full report will be saved to file)")
    
    def display_file_save_result(self, file_paths):
        """Display information about saved files"""
        print(f"\n✅ Report saved to: {file_paths['timestamp_path']}")
        print(f"✅ Report also saved with readable name: {file_paths['readable_path']}")
        print(f"\n📂 All reports are stored in the research_reports directory")

    def display_research_with_citations(self, task, result, citations):
        """Display the result of a research task with citations"""
        if isinstance(result, str) and result.startswith("Error:"):
            print(f"⚠️ Research task (LLM: '{task}') failed: {result}")
        else:
            print(f"📄 Result snippet (LLM: '{task}'):\n{result[:200].strip()}...")
            if citations and len(citations) > 0:
                print(f"📚 Found {len(citations)} sources:")
                for i, citation in enumerate(citations[:3]):  # Show first 3 citations
                    title = citation.get("title", "Untitled")
                    url = citation.get("url", "No URL")
                    print(f"  [{i+1}] {title}: {url}")
                if len(citations) > 3:
                    print(f"  ... and {len(citations)-3} more sources") 