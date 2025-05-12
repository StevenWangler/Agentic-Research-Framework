# Agentic Research Framework

A powerful framework for AI-driven research that utilizes a team of specialized agents to produce comprehensive research reports from natural language queries.

## Overview

This project implements an agentic research system that breaks down the research process into specialized components:

- **Planner Agent**: Generates a structured research plan based on the user query
- **Clarifier Agent**: Asks clarifying questions to better understand research needs
- **Research Agent**: Conducts web searches and gathers information
- **Critique Agent**: Evaluates research findings for quality and relevance
- **Synthesizer Agent**: Combines and structures research findings
- **Writer Agent**: Produces the final research report

Each agent is powered by OpenAI models and works together in a coordinated workflow to produce high-quality research reports.

## Features

- Collaborative multi-agent architecture for comprehensive research
- Interactive clarification system to refine queries
- Web search integration for up-to-date information
- Automated report generation with critique and synthesis
- Configurable models for each agent (GPT-3.5-Turbo, GPT-4, etc.)
- Persistent storage of research reports

## Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
   ```
   git clone
   cd Agentic-Research-Framework
   ```

2. Install dependencies:
   ```
   pip install -r Research\ Team/requirements.txt
   ```

3. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_ORG_ID=your_organization_id  # Optional
   ```

### Running the Application

Navigate to the Research Team directory and run the main script:

```
cd Research Team
python main.py
```

Follow the interactive prompts to:
1. Enter your research query
2. Answer clarifying questions (if any)
3. Wait for the agents to generate your research report

Research reports will be saved in the `Research Team/research_reports` directory.

## Project Structure

```
Research Team/
├── agents/                     # Agent implementations
│   ├── planner_agent.py        # Research planning
│   ├── clarifier_agent.py      # Query clarification
│   ├── research_agent.py       # Web research
│   ├── critique_agent.py       # Research evaluation
│   ├── synthesiser_agent.py    # Information synthesis
│   └── writer_agent.py         # Report generation
├── tools/                      # Utility tools
│   └── web_tools.py            # Web search functionality
├── prompts/                    # Agent prompts
├── research_reports/           # Generated reports
├── main.py                     # Main application
└── requirements.txt            # Dependencies
```

## Customization

You can customize the model used by each agent by modifying the `agent_model_configs` dictionary in `main.py`. For example:

```python
agent_model_configs = {
    "PlannerAgent": "gpt-3.5-turbo",
    "ClarifierAgent": "gpt-3.5-turbo",
    "ResearchAgent": "gpt-4.1-turbo-preview",
    "CritiqueAgent": "gpt-4",
    "SynthesiserAgent": "gpt-4.1-turbo-preview",
    "WriterAgent": "gpt-3.5-turbo",
}
```

## License

This project is licensed under the terms of the included LICENSE file.