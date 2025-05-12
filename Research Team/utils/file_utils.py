import os
import re
import datetime

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

def save_report_to_file(report_content, initial_query, reports_dir):
    """Save research report to file with a readable name and timestamp"""
    # Create reports directory if it doesn't exist
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        
    # Create filenames
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = create_safe_filename(initial_query)
    readable_filename = f"{safe_query}_{timestamp}.md"
    
    readable_path = os.path.join(reports_dir, readable_filename)
    
    # Save files
    try:
        with open(readable_path, "w", encoding="utf-8") as f:
            f.write(f"# Report for Query: {initial_query}\n\n")
            f.write(report_content)
            
        return {
            "timestamp_path": readable_path,
            "readable_path": readable_path
        }
    except IOError as e:
        raise IOError(f"Could not save report to file: {e}") 