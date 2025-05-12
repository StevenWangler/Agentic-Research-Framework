import re
import json

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

def display_clean_report(report_text):
    """Clean and display the final report output without JSON formatting"""
    # Remove any JSON or object representation format
    
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