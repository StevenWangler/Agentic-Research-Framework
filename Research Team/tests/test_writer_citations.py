#!/usr/bin/env python3
"""
Simple test script to verify citation handling in the WriterAgent.
"""

import asyncio
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MockKernel:
    def __init__(self):
        self.response = None
    
    def add_function(self, function_name, plugin_name, prompt, description):
        # Mock the kernel.add_function method
        class MockFunction:
            def __init__(self, name):
                self.name = name
        return MockFunction(function_name)
    
    async def invoke(self, function, arguments, service_id=None):
        # Return the mocked response
        return self.response


async def test_writer_citations():
    """Test the WriterAgent's handling of citations"""
    print("🧪 Starting WriterAgent citation test...")
    
    # Import the writer agent
    try:
        from agents.writer_agent import WriterAgent
    except ImportError as e:
        print(f"❌ Error importing WriterAgent: {e}")
        return
    
    # Create a mock kernel
    mock_kernel = MockKernel()
    
    # Set up mock response for different test cases
    mock_kernel.response = """# AI and Drug Discovery Research Report

## Introduction
This is a report about AI in drug discovery.

## Key Findings
AI is transforming drug discovery processes.

## Methods
Various machine learning approaches are being used.

## Conclusion
AI will continue to revolutionize the pharmaceutical industry.

## References
Some references go here.
"""
    
    # Path to prompts (doesn't matter for the mock)
    prompts_path = "prompts"
    
    # Create a writer agent
    try:
        writer = WriterAgent(mock_kernel, prompts_path)
        print("✅ WriterAgent created with mock kernel")
    except Exception as e:
        print(f"❌ Error creating WriterAgent: {e}")
        return
    
    # Test cases for citation handling
    test_cases = [
        {
            "name": "Citations section exists",
            "input": """This is a synthesized report about AI in drug discovery.
It contains some information about the topic.

## Sources and Citations
1. [Article about AI](https://example.com/ai)
2. [Drug Discovery Journal](https://example.com/drugs)
"""
        },
        {
            "name": "No citations section",
            "input": """This is a report without any citations.
Just some plain text content.
"""
        },
        {
            "name": "Empty report",
            "input": ""
        },
        {
            "name": "Error report",
            "input": "Error: Could not complete research due to insufficient data."
        }
    ]
    
    # Run test cases
    for i, test_case in enumerate(test_cases):
        print(f"\n📋 Test Case {i+1}: {test_case['name']}")
        
        result = await writer.format_report_as_markdown(
            "AI in Drug Discovery", 
            test_case["input"]
        )
        
        print(f"✅ Writer produced formatted report ({len(result)} characters)")
        
        # Check if the formatted report contains citations
        if "## Sources and Citations" in result:
            citation_section = result.split("## Sources and Citations")[1].strip()
            print(f"✓ Citation section found in output with {citation_section.count('](http')} citations")
            print("--- CITATION SECTION PREVIEW ---")
            print(citation_section[:200] + ("..." if len(citation_section) > 200 else ""))
            print("--- END PREVIEW ---")
        elif "## References" in result or "## Sources" in result or "## Bibliography" in result:
            # Check alternative section titles
            section_titles = ["## References", "## Sources", "## Bibliography"]
            for title in section_titles:
                if title in result:
                    section = result.split(title)[1].strip()
                    print(f"✓ {title.strip('#')} section found with {section.count('](http')} citations")
                    break
        else:
            print("✗ No citations section found in output")
        
        # Check if original citations were preserved
        if "## Sources and Citations" in test_case["input"] and "## Sources and Citations" in result:
            print("✓ Original citations were preserved")
        elif "## Sources and Citations" in test_case["input"] and "## Sources and Citations" not in result:
            print("✗ Original citations were LOST")
    
    print("\n✅ WriterAgent citation tests completed")


if __name__ == "__main__":
    asyncio.run(test_writer_citations()) 