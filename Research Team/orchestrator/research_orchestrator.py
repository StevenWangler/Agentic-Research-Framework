import re
from agents.planner_agent import PlannerAgent
from agents.clarifier_agent import ClarifierAgent
from agents.research_agent import ResearchAgent
from agents.critique_agent import CritiqueAgent
from agents.synthesiser_agent import SynthesiserAgent
from agents.writer_agent import WriterAgent
from utils.text_utils import extract_clarification_insights
from utils.file_utils import save_report_to_file

class ResearchOrchestrator:
    def __init__(self, config_manager, kernel, ui):
        """Initialize the research orchestrator
        
        Args:
            config_manager: The configuration manager instance
            kernel: The semantic kernel instance
            ui: The user interface instance
        """
        self.config = config_manager
        self.kernel = kernel
        self.ui = ui
        self.agent_service_ids = {}
        self.init_agents()
        
    def init_agents(self):
        """Initialize all agent instances"""
        # Get service IDs for each agent from the config manager
        self.agent_service_ids = self.config.setup_kernel_services(self.kernel)
        
        # Initialize agent instances with appropriate service IDs
        self.planner = PlannerAgent(
            self.kernel, 
            self.config.prompts_path, 
            service_id=self.agent_service_ids["PlannerAgent"]
        )
        self.clarifier = ClarifierAgent(
            self.kernel, 
            self.config.prompts_path, 
            service_id=self.agent_service_ids["ClarifierAgent"]
        )
        self.researcher = ResearchAgent(
            self.kernel, 
            self.config.prompts_path, 
            service_id=self.agent_service_ids["ResearchAgent"]
        )
        self.critique_agent = CritiqueAgent(
            self.kernel, 
            self.config.prompts_path, 
            service_id=self.agent_service_ids["CritiqueAgent"]
        )
        self.synthesiser_agent = SynthesiserAgent(
            self.kernel, 
            self.config.prompts_path, 
            service_id=self.agent_service_ids["SynthesiserAgent"]
        )
        self.writer_agent = WriterAgent(
            self.kernel, 
            self.config.prompts_path, 
            service_id=self.agent_service_ids["WriterAgent"]
        )
    
    async def execute_research_pipeline(self, initial_query):
        """Execute the complete research pipeline
        
        Args:
            initial_query: The initial research query from the user
            
        Returns:
            dict: Results of the research process
        """
        # Clarification Phase
        current_query, clarification_insights = await self._handle_clarification_phase(initial_query)
        
        # Planning Phase
        current_plan = await self._handle_planning_phase(current_query, clarification_insights)
        if current_plan.startswith("Error:"):
            return await self._handle_error(initial_query, current_plan)
            
        # Research Phase
        research_outputs = await self._handle_research_phase(current_query, current_plan, clarification_insights)
        if not research_outputs:
            error_msg = "No research tasks were identified/executed. Cannot proceed to critique."
            return await self._handle_error(initial_query, error_msg)
            
        # Critique Phase
        critiqued_documents = await self._handle_critique_phase(research_outputs)
        if not critiqued_documents:
            error_msg = "No documents were successfully critiqued. Cannot proceed to synthesis."
            return await self._handle_error(initial_query, error_msg)
            
        # Synthesis Phase
        synthesized_report = await self._handle_synthesis_phase(current_query, critiqued_documents)
        if synthesized_report.startswith("Error:"):
            return await self._handle_error(initial_query, synthesized_report)
            
        # Writing Phase
        final_report = await self._handle_writing_phase(initial_query, synthesized_report)
        
        # Save report to file
        file_paths = save_report_to_file(
            final_report.replace('\\n', '\n'), 
            initial_query, 
            self.config.reports_dir
        )
        self.ui.display_file_save_result(file_paths)
        
        return {
            "initial_query": initial_query,
            "final_report": final_report,
            "file_paths": file_paths
        }
    
    async def _handle_clarification_phase(self, initial_query):
        """Handle the clarification phase of research
        
        Args:
            initial_query: The initial research query
            
        Returns:
            tuple: (current_query, clarification_insights)
        """
        print(f"\n❓ Generating clarifying questions for: \"{initial_query}\"")
        clarifying_questions = await self.clarifier.generate_clarifying_questions(initial_query)
        
        if clarifying_questions.startswith("Error:"):
            print(f"Error generating clarifying questions: {clarifying_questions}")
            print("Proceeding with the initial query.")
            return initial_query, ""
            
        user_clarifications = self.ui.get_clarification_responses(clarifying_questions)
        
        # Combine the original query with clarifications if provided
        current_query = initial_query
        if user_clarifications.strip():
            current_query = f"{initial_query}\n\nAdditional clarifications provided by user:\n{user_clarifications}"
            
        self.ui.display_clarification_status(bool(user_clarifications.strip()))
        
        return current_query, ""  # No insights yet
    
    async def _handle_planning_phase(self, current_query, clarification_insights):
        """Handle the planning phase of research
        
        Args:
            current_query: The current query after clarification
            clarification_insights: Any insights from clarification
            
        Returns:
            str: The final research plan
        """
        print(f"\n🚀 Generating research plan for: \"{current_query}\"")
        initial_plan_str = await self.planner.generate_plan(current_query)
        
        self.ui.display_plan(initial_plan_str)
        
        if initial_plan_str.startswith("Error:"):
            return initial_plan_str
            
        print("\n🤔 Checking if clarification is needed...")
        clarification_output = await self.clarifier.clarify_query(current_query, initial_plan_str)
        
        # Handle different clarifier outputs
        if "CLARIFICATION_NOT_NEEDED" in clarification_output:
            print("✅ Query and plan are clear. Proceeding.")
            return initial_plan_str
        elif clarification_output.startswith("QUESTIONS:"):
            print("\n❓ Clarification would be helpful, but proceeding autonomously:")
            print(clarification_output.replace("QUESTIONS:", "").strip())
            print("\n✅ Continuing with research using the initial plan...")
            
            # Extract insights from clarification questions
            new_insights = extract_clarification_insights(clarification_output)
            if new_insights:
                self.ui.display_clarification_insights(new_insights)
                return initial_plan_str, new_insights
            return initial_plan_str
        elif clarification_output.startswith("Error:"):
            print(f"Clarifier Agent failed: {clarification_output}. Proceeding with initial plan.")
            return initial_plan_str
        else:
            print(f"⚠️ Unexpected output from ClarifierAgent: {clarification_output}")
            print("Assuming clarification is not strictly needed and proceeding with initial plan.")
            return initial_plan_str
    
    async def _handle_research_phase(self, current_query, current_plan, clarification_insights):
        """Handle the research phase
        
        Args:
            current_query: The current query
            current_plan: The research plan
            clarification_insights: Insights from clarification phase
            
        Returns:
            list: The research outputs
        """
        # Extract research tasks from the plan
        research_tasks = self.planner.extract_research_tasks_from_plan(current_plan)
        
        if not research_tasks:
            return []
        
        research_outputs = []
        
        for task in research_tasks:
            self.ui.display_research_start(task)
            
            # Perform research and store the result
            result = await self.researcher.perform_research_task(
                task, 
                search_query_for_web=None,
                additional_guidance=clarification_insights
            )
            
            # Check if result is in the new dict format with citations or old string format
            if isinstance(result, dict) and "text" in result:
                result_text = result["text"]
                citations = result.get("citations", [])
                # Save citations with the research output
                research_outputs.append({
                    "task": task, 
                    "content": result_text,
                    "citations": citations
                })
                self.ui.display_research_result(task, result_text)
            else:
                # Handle legacy string format
                research_outputs.append({
                    "task": task, 
                    "content": result,
                    "citations": []
                })
                self.ui.display_research_result(task, result)
            
        return research_outputs
    
    async def _handle_critique_phase(self, research_outputs):
        """Handle the critique phase
        
        Args:
            research_outputs: The research outputs
            
        Returns:
            list: Critiqued documents
        """
        print("\n🧐 Starting Critique Phase...")
        critiqued_documents = []
        
        for res_output in research_outputs:
            task_desc = res_output["task"]
            doc_text = res_output["content"]
            doc_citations = res_output.get("citations", [])
            
            self.ui.display_critique_start(task_desc)
            critique = await self.critique_agent.critique_document(task_desc, doc_text)
            
            critiqued_documents.append({
                "task": task_desc,
                "original": doc_text,
                "critique": critique,
                "citations": doc_citations
            })
            
            self.ui.display_critique_result(critique)
        
        return critiqued_documents
    
    async def _handle_synthesis_phase(self, current_query, critiqued_documents):
        """Handle the synthesis phase
        
        Args:
            current_query: The current query
            critiqued_documents: The critiqued documents
            
        Returns:
            str: The synthesized report
        """
        self.ui.display_synthesis_start()
        
        # Collect all citations from critiqued documents
        all_citations = []
        citation_count = 0
        for doc in critiqued_documents:
            if isinstance(doc, dict) and "citations" in doc:
                doc_citations = doc.get("citations", [])
                citation_count += len(doc_citations)
                all_citations.extend(doc_citations)
        
        # Log citation count for debugging
        if citation_count > 0:
            print(f"📚 Found {citation_count} total citations from all research documents")
        
        # Convert documents to expected format for synthesiser
        docs_for_synthesis = []
        for doc in critiqued_documents:
            if isinstance(doc, dict):
                if "critique" in doc and "original" in doc:
                    # This is from critique phase with new format
                    docs_for_synthesis.append({
                        "content": doc["critique"],
                        "original_task": doc.get("task", "Unknown task"),
                        "original_content": doc["original"]
                    })
        
        # Verify we have documents to synthesize
        if not docs_for_synthesis:
            return "Error: No critiqued documents provided for synthesis."
        
        synthesized_report = await self.synthesiser_agent.synthesise_research(
            current_query, 
            docs_for_synthesis
        )
        
        # Attach citations to the synthesized report
        if not synthesized_report.startswith("Error:") and all_citations:
            # Add a clear citations section at the end of the report
            synthesized_report += "\n\n## Sources and Citations\n\n"
            
            # Deduplicate citations by URL and clean tracking parameters
            unique_citations = {}
            for citation in all_citations:
                url = citation.get("url", "")
                
                # Clean tracking parameters from URLs
                clean_url = url
                if "?utm_source=" in url:
                    clean_url = url.split("?utm_source=")[0]
                elif "?" in url and ("&utm_" in url or "&amp;utm_" in url):
                    # Handle more complex URLs with multiple parameters
                    base_url = url.split("?")[0]
                    params = url.split("?")[1].split("&")
                    non_tracking_params = [p for p in params if not p.startswith("utm_") and not p.startswith("amp;utm_")]
                    if non_tracking_params:
                        clean_url = base_url + "?" + "&".join(non_tracking_params)
                    else:
                        clean_url = base_url
                
                if clean_url and clean_url not in unique_citations:
                    title = citation.get("title", "Untitled Source")
                    
                    # Skip empty or generic titles
                    if not title or title.lower() in ["source", "untitled source", "untitled"]:
                        # Try to extract a better title from the URL
                        if "://" in clean_url:
                            domain = clean_url.split("://")[1].split("/")[0]
                            path = "/".join(clean_url.split("/")[3:]).split("?")[0]
                            if path:
                                title = f"Article from {domain}: {path}"
                            else:
                                title = f"Source: {domain}"
                    
                    unique_citations[clean_url] = {
                        "title": title,
                        "url": clean_url
                    }
            
            # Sort citations for consistent ordering
            sorted_citations = sorted(
                unique_citations.values(), 
                key=lambda x: x.get("title", "").lower()
            )
            
            # Add the unique citations to the report
            if sorted_citations:
                print(f"📋 Adding {len(sorted_citations)} unique citations to the report")
                for i, citation in enumerate(sorted_citations):
                    title = citation.get("title", "Untitled Source")
                    url = citation.get("url", "No URL provided")
                    synthesized_report += f"{i+1}. [{title}]({url})\n"
            else:
                print("⚠️ No citations found to add to the report")
                synthesized_report += "*No citations were found for this report.*\n"
        
        if not synthesized_report.startswith("Error:"):
            self.ui.display_synthesis_stats(synthesized_report)
        
        return synthesized_report
    
    async def _handle_writing_phase(self, initial_query, synthesized_report):
        """Handle the writing phase
        
        Args:
            initial_query: The initial query
            synthesized_report: The synthesized research report
            
        Returns:
            str: The final formatted report
        """
        print("\n✍️ Starting Report Writing Phase...")
        
        final_markdown_report = await self.writer_agent.format_report_as_markdown(
            initial_query, 
            synthesized_report
        )
        
        self.ui.display_final_report(final_markdown_report)
        
        return final_markdown_report
    
    async def _handle_error(self, initial_query, error_message):
        """Handle an error in the research pipeline
        
        Args:
            initial_query: The initial research query
            error_message: The error message
            
        Returns:
            dict: Error results
        """
        # Even if there's an error, we might want the Writer to format it nicely
        final_markdown_report = await self.writer_agent.format_report_as_markdown(
            initial_query, 
            error_message
        )
        
        self.ui.display_final_report(final_markdown_report)
        
        file_paths = save_report_to_file(
            final_markdown_report.replace('\\n', '\n'), 
            initial_query, 
            self.config.reports_dir
        )
        self.ui.display_file_save_result(file_paths)
        
        return {
            "initial_query": initial_query,
            "error": error_message,
            "final_report": final_markdown_report,
            "file_paths": file_paths
        } 