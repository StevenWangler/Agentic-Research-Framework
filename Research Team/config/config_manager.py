import os
import json
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

class ConfigManager:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # API credentials
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.org_id = os.getenv("OPENAI_ORG_ID")
        
        # Default model settings
        self.default_model_id = "gpt-4.1-nano"
        self.agent_model_configs = {}
        
        # Path configurations
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.reports_dir = os.path.join(self.base_path, "research_reports")
        self.prompts_path = os.path.join(self.base_path, "prompts")
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load model configurations
        self.load_model_config()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            print(f"📁 Created research reports directory: {self.reports_dir}")
        
    def load_model_config(self):
        """Load model configurations from JSON file"""
        config_path = os.path.join(self.base_path, "config", "agent_models.json")
        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                self.default_model_id = config.get("default_model_id", self.default_model_id)
                self.agent_model_configs = config.get("agent_model_configs", {})
                print(f"✅ Loaded agent model configurations from {config_path}")
        except Exception as e:
            print(f"⚠️ Error loading configuration file: {e}")
            print("Using default configuration instead.")
            self.agent_model_configs = {
                "PlannerAgent": "gpt-4.1-nano",
                "ClarifierAgent": "gpt-4.1-nano",
                "ResearchAgent": "gpt-4.1-turbo-preview",
                "CritiqueAgent": "gpt-4.1-nano",
                "SynthesiserAgent": "gpt-4.1-turbo-preview",
                "WriterAgent": "gpt-4.1-nano",
            }
    
    def setup_kernel_services(self, kernel):
        """Configure and register all AI services for the kernel"""
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables (OPENAI_API_KEY)")
        
        # Track registered services and their associations with agents
        registered_services = {}
        agent_service_ids = {}
        
        # Register default service
        default_service_id = f"default_{self.default_model_id.replace('.', '_').replace('-', '_')}_service"
        kernel.add_service(
            OpenAIChatCompletion(
                service_id=default_service_id,
                ai_model_id=self.default_model_id,
                api_key=self.api_key,
                org_id=self.org_id
            )
        )
        registered_services[self.default_model_id] = default_service_id
        
        # Register services for each agent based on their config
        agent_classes = ["PlannerAgent", "ClarifierAgent", "ResearchAgent", 
                        "CritiqueAgent", "SynthesiserAgent", "WriterAgent"]
                        
        for agent_name in agent_classes:
            model_id = self.agent_model_configs.get(agent_name, self.default_model_id)
            
            if model_id not in registered_services:
                service_id = f"{agent_name.lower()}_{model_id.replace('.', '_').replace('-', '_')}_service"
                kernel.add_service(
                    OpenAIChatCompletion(
                        service_id=service_id,
                        ai_model_id=model_id,
                        api_key=self.api_key,
                        org_id=self.org_id
                    )
                )
                registered_services[model_id] = service_id
            
            # Store the service_id that this agent should use
            agent_service_ids[agent_name] = registered_services[model_id]
        
        return agent_service_ids 