import asyncio
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
import re
from dotenv import load_dotenv
from agents.writer_agent import WriterAgent
from tools.web_tools import WebSearchPlugin
import traceback

# Import our new modules
from config.config_manager import ConfigManager
from orchestrator.research_orchestrator import ResearchOrchestrator
from ui.console_interface import ConsoleInterface

load_dotenv() # New line: load environment variables from .env file

# Import agent classes
from agents.planner_agent import PlannerAgent
from agents.clarifier_agent import ClarifierAgent
from agents.research_agent import ResearchAgent
from agents.critique_agent import CritiqueAgent
from agents.synthesiser_agent import SynthesiserAgent

# Function to extract potential clarification insights from questions
def extract_clarification_insights(clarification_questions):
    """Extract useful insights from clarification questions to help guide research"""
    if not clarification_questions or not clarification_questions.strip():
        return ""
        
    # Remove the QUESTIONS: prefix if present
    questions_text = clarification_questions.replace("QUESTIONS:", "").strip()
    
    # Extract individual questions
    questions = []
    for line in questions_text.split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line[0] == '-' or line[0] == '*'):
            questions.append(line.lstrip('0123456789.-* '))
    
    if not questions:
        questions = questions_text.split('?')
        questions = [q.strip() + '?' for q in questions if q.strip()]
    
    # Generate insights
    insights = "Additional research guidance based on potential clarifications:\n"
    for q in questions:
        # Extract key terms and concepts from the question
        q = q.rstrip('?')
        terms = [term.strip() for term in q.split() if len(term) > 3 and term.lower() not in 
                ('what', 'when', 'where', 'which', 'would', 'could', 'should', 'about', 'interested', 'specific', 'there', 'these', 'those')]
        
        if terms:
            insights += f"- Consider exploring: {', '.join(terms)}\n"
    
    return insights

# Function to display clean output from the final report
def display_clean_report(report_text):
    """Clean and display the final report output without JSON formatting"""
    # Remove any JSON or object representation format
    import re
    import json
    
    # If it looks like JSON, try to parse it
    if report_text.strip().startswith('{') and report_text.strip().endswith('}'):
        try:
            json_obj = json.loads(report_text)
            if isinstance(json_obj, dict) and 'content' in json_obj:
                return json_obj['content']
        except:
            pass
    
    # Look for content within ChatMessageContent objects
    content_pattern = r'inner_content=.*?\((.*?)\)'
    matches = re.findall(content_pattern, report_text)
    if matches:
        for match in matches:
            if 'content=' in match:
                content_match = re.search(r'content=["\']([^"\']+)["\']', match)
                if content_match:
                    return content_match.group(1)
    
    # Try to clean up common formats
    report_text = re.sub(r'ChatMessageContent\(.*?\)', '', report_text)
    report_text = re.sub(r'ChatCompletion\(.*?\)', '', report_text)
    
    return report_text

# Function to create a safe filename from the query
def create_safe_filename(query, max_length=50):
    """Create a safe filename from the query string"""
    # Replace problematic characters with underscores
    safe_name = re.sub(r'[^\w\s-]', '_', query.lower())
    safe_name = re.sub(r'[\s-]+', '_', safe_name)
    # Truncate if necessary
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
    # Remove trailing underscores
    safe_name = safe_name.strip('_')
    return safe_name

async def main():
    try:
        # Initialize the configuration manager
        config_manager = ConfigManager()
        
        # Initialize the semantic kernel
        kernel = sk.Kernel()
        
        # Initialize the UI
        ui = ConsoleInterface()
        
        # Register plugins
        web_search_plugin = WebSearchPlugin(
            model="gpt-4.1",
            temperature=0.5,
            default_count=10,
            max_tokens=4096,
            simulate_delay=False
        )
        try:
            kernel.import_native_plugin_from_object(web_search_plugin, "WebSearch")
            print("🛠️ WebSearchPlugin registered.")
        except Exception as e:
            print(f"⚠️ WebSearchPlugin registration error: {e}. Will attempt to use it directly.")
            # Set as global for direct access if needed
            global web_search_plugin_instance
            web_search_plugin_instance = web_search_plugin
        
        # Initialize the research orchestrator
        orchestrator = ResearchOrchestrator(config_manager, kernel, ui)
        
        # Get the initial query from the user
        initial_user_query = ui.get_initial_query()
        
        # Execute the research pipeline
        await orchestrator.execute_research_pipeline(initial_user_query)
        
    except ValueError as e:
        print(f"💥 Configuration error: {e}")
    except Exception as e:
        print(f"An unhandled error occurred in the main loop: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting application...")
    except Exception as e:
        # This secondary try-except is for errors during asyncio.run itself or very early errors
        print(f"A critical error occurred: {e}")
        traceback.print_exc() 