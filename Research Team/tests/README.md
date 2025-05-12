# Test Scripts

This directory contains test scripts for verifying functionality of different components in the Agentic Research Framework.

## Available Tests

### Citation Testing

- `test_citation_report.py`: Tests citation handling in the full research pipeline
- `test_writer_citations.py`: Tests specifically the WriterAgent's handling of citations

## Running Tests

To run individual tests, navigate to the Research Team directory and execute:

```bash
python -m tests.test_citation_report
python -m tests.test_writer_citations
``` 