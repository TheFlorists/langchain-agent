# show_front_page
# preview_html
# get_tabs

import io
import re
from typing import List, Dict, Optional
import PyPDF2
from canvasapi import Canvas
import docx
from dotenv import load_dotenv
import os
import json
import time
import zipfile
import requests
import pickle
from datetime import datetime, timedelta
load_dotenv("secrets.env")

def get_course_info(canvas, course_id: int) -> Optional[List[Dict]]:
    """
    Fetch all sections for a specific course
    
    Args:
        canvas: Canvas instance
        course_id (int): The ID of the course to fetch sections from
        
    Returns:
        List[Dict]: List of section dictionaries, or None if there's an error
    """
    try:
        course = canvas.get_course(course_id)
        tabs = course.get_tabs()

        course_info = []
        for tab in tabs:
            print(tab)
            tab_dict = {
                'id': tab.id,
                'html_url': tab.html_url,
                'full_url': tab.full_url,
                'position': tab.position,
                'label': tab.label,
                'type': tab.type,
                'hidden': getattr(tab, 'hidden', False),
                'visibility': getattr(tab, 'visibility', None),
                'is_hidden': getattr(tab, 'is_hidden', False),
                'is_external': getattr(tab, 'is_external', False),
                'external_url': getattr(tab, 'external_url', None),
            }
            course_info.append(tab_dict)

        return course_info
    
    except Exception as e:
        print(f"Error fetching course info for course {course_id}: {str(e)}")
        return None

def get_cached_export(course_id: int, max_age_hours: int = 24) -> Optional[Dict]:
    """
    Try to get a cached export for the course
    
    Args:
        course_id (int): The course ID
        max_age_hours (int): Maximum age of cache in hours
        
    Returns:
        Dict: Cached export data if valid, None otherwise
    """
    cache_file = f"cache/course_{course_id}_export.pkl"
    
    if not os.path.exists("cache"):
        os.makedirs("cache")
        
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            # Check if cache is still valid
            cache_time = cached_data.get('timestamp')
            if cache_time and datetime.now() - cache_time < timedelta(hours=max_age_hours):
                print(f"Using cached export from {cache_time}")
                return cached_data
        except Exception as e:
            print(f"Error reading cache: {str(e)}")
    
    return None

def save_to_cache(course_id: int, export_data: Dict):
    """Save export data to cache"""
    cache_file = f"cache/course_{course_id}_export.pkl"
    
    try:
        # Add timestamp to the export data
        export_data['timestamp'] = datetime.now()
        
        with open(cache_file, 'wb') as f:
            pickle.dump(export_data, f)
        print(f"Saved export to cache: {cache_file}")
    except Exception as e:
        print(f"Error saving to cache: {str(e)}")

def get_cached_zip(course_id: int, max_age_hours: int = 24) -> Optional[bytes]:
    """
    Try to get a cached zip file for the course
    
    Args:
        course_id (int): The course ID
        max_age_hours (int): Maximum age of cache in hours
        
    Returns:
        bytes: Cached zip content if valid, None otherwise
    """
    cache_file = f"cache/course_{course_id}_export.zip"
    cache_meta = f"cache/course_{course_id}_meta.json"
    
    if not os.path.exists("cache"):
        os.makedirs("cache")
        
    if os.path.exists(cache_file) and os.path.exists(cache_meta):
        try:
            with open(cache_meta, 'r') as f:
                meta = json.load(f)
            cache_time = datetime.fromisoformat(meta['timestamp'])
            
            if datetime.now() - cache_time < timedelta(hours=max_age_hours):
                print(f"Using cached zip from {cache_time}")
                with open(cache_file, 'rb') as f:
                    return f.read()
        except Exception as e:
            print(f"Error reading cache: {str(e)}")
    
    return None

def save_zip_to_cache(course_id: int, zip_content: bytes):
    """Save zip content to cache"""
    cache_file = f"cache/course_{course_id}_export.zip"
    cache_meta = f"cache/course_{course_id}_meta.json"
    
    try:
        if not os.path.exists("cache"):
            os.makedirs("cache")
            
        # Save zip file
        with open(cache_file, 'wb') as f:
            f.write(zip_content)
            
        # Save metadata
        meta = {
            'timestamp': datetime.now().isoformat(),
            'course_id': course_id
        }
        with open(cache_meta, 'w') as f:
            json.dump(meta, f)
            
        print(f"Saved zip to cache: {cache_file}")
    except Exception as e:
        print(f"Error saving to cache: {str(e)}")

import re

def clean_pdf_text(content):
    """
    Enhanced PDF text cleanup with additional processing steps for academic slides
    
    Args:
        content (str): Raw text content from PDF
        
    Returns:
        str: Cleaned, readable text content
    """
    # Step 1: Fix Unicode escape sequences (expanded list)
    unicode_map = {
        '\\u201c': '"', '\\u201d': '"',
        '\\u00f6': 'ö', '\\u00e9': 'é',
        '\\u00e1': 'á', '\\u00a0': ' ',
        '\\u2019': "'", '\\u2013': '-',
        '\\u2014': '—', '\\u2026': '...',
        '\\u00f6s': 'ös', '\\u00e9nyi': 'ényi',
        '\\u2022': '•', '\\u00fb': 'û',
        '\\u00ff': 'ÿ', '\\ufb01': 'fi',
        '\\ufb02': 'fl', '\\u00a0': ' ',
        '\\u00f6\\': 'ö', '\\u00e9\\': 'é',
        '\\u25cf': '●', '\\u25cb': '○',
        '\\u2713': '✓', '\\u03b2': 'β',
        '\\u03b3': 'γ', '\\u221e': '∞'
    }
    for escaped, char in unicode_map.items():
        content = content.replace(escaped, char)
    
    # Step 2: Fix literal newlines and fix common PDF extraction issues
    content = content.replace('\\n', '\n')
    
    # Step 3: Remove null bytes and other control characters
    content = re.sub(r'\u0000+', '', content)
    content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
    
    # Step 4: Remove JSON artifacts (from your sample data)
    content = re.sub(r'"filename":\s*"[^"]+\.pdf",\s*"content":\s*"', '\n\n--- NEW SLIDE SET: ', content)
    content = re.sub(r'",\s*"type":\s*"pdf"', '', content)
    
    # Step 5: Remove matrix-like structures and mathematical notation
    content = re.sub(r'266664.*?377775', '', content, flags=re.DOTALL)
    content = re.sub(r'\[A\^?n\]i,j.*?edges', '', content, flags=re.DOTALL)
    content = re.sub(r'<latexit.*?</latexit>', '', content, flags=re.DOTALL)
    content = re.sub(r'\\\w+\{.*?\}', '', content)
    
    # Step 6: Remove specific patterns for common slide elements
    slide_patterns = [
        r'\d+\s*x\s*\d+',  # Dimensions like "3 x 3"
        r'p\s*=\s*0\.\d+',  # Probability notation
        r'\(\d+,\s*\d+\)',  # Coordinate pairs
        r'\b[0-9]+\.[0-9]+\b',  # Decimal numbers
        r'^\s*\d{1,2}\s*$',  # Standalone numbers (slide numbers)
        r'^\s*[A-Z]\d\s*$',  # Notation like "A2"
        r'^\s*[a-zA-Z]{1,2}\s*$',  # Single letters
        r'i,j',  # Matrix notation
        r'dI/dt',  # Differential equations
        r'[kK]_\w+',  # Variables with subscripts
        r'A\d+',  # Matrix notation
    ]
    for pattern in slide_patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    # Step 7: Handle PDF slide headers and footers
    content = re.sub(r'Memes, Measles, and Misinformation', 'COURSE: Memes, Measles, and Misinformation', content)
    
    # Step 8: Remove lines containing only a single type of character
    content = re.sub(r'^\s*(.)\1{3,}\s*$', '', content, flags=re.MULTILINE)
    
    # Step 9: Remove lines that likely represent code or formulas
    code_patterns = [
        r'^\s*import\s+\w+.*$',
        r'^\s*random_nums\s*=.*$',
        r'^\s*if\s*\(.*\):.*$',
        r'.*=\s*\[\[.*\]\].*$',
        r'.*\.add_\w+\(.*\).*$',
        r'^\s*g\s*=\s*nx\..*$',
        r'for\s+i\s+in\s+range.*$',
        r'.*pyplot\..*$',
        r'.*\.decode\(.*\).*$',
        r'.*zip_ref\..*$',
        r'Nt\+1\s*=\s*Nt.*',  # Mathematical equations
        r'ddt=.*',            # More differential equations
        r'.*=.*\(\s*.*\)',    # Function calls
        r'.*\[.*\].*=.*',     # Array assignments
    ]
    for pattern in code_patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    # Step 10: Split into lines and filter problematic ones
    lines = content.split('\n')
    filtered_lines = []
    
    prev_line = ""
    for line in lines:
        line = line.strip()
        
        # Skip empty lines or too short lines
        if not line or len(line) < 2:
            continue
            
        # Skip lines that are likely slide artifacts
        if re.match(r'^[0-9]+$', line) or re.match(r'^[A-Z][0-9]$', line):
            continue
            
        # Skip lines with too many numbers or special characters
        if sum(c.isdigit() for c in line) > len(line) * 0.5:
            continue
            
        # Skip very short lines that are likely labels
        if len(line) <= 3 and not line.lower() in ['the', 'and', 'but', 'or', 'a', 'an']:
            continue
        
        # Avoid duplicating the same line that appears consecutively
        if line == prev_line:
            continue
            
        # Add the line to our filtered list
        filtered_lines.append(line)
        prev_line = line
    
    # Step 11: Join lines and fix multiple newlines
    content = '\n'.join(filtered_lines)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Step 12: Fix spacing issues
    content = re.sub(r'\s{2,}', ' ', content)
    
    # Step 13: Fix academic-specific patterns
    content = re.sub(r'•', '- ', content)  # Convert bullets to dashes
    content = re.sub(r'–', '-', content)   # Standardize dashes
    
    # Step 14: Clean up remaining specific patterns from the sample data
    content = re.sub(r'In Class Points[!]?', '\n[In-Class Activity]', content)
    content = re.sub(r'https?://\S+', lambda m: f"\n{m.group(0)}\n", content)  # Put URLs on their own lines
    
    return content.strip()

def process_course_content(content_list):
    """
    Process and clean course content from various file types
    
    Args:
        content_list (List[Dict]): List of content dictionaries with filename and content
        
    Returns:
        List[Dict]: Processed content with cleaned text
    """
    processed_content = []
    
    for item in content_list:
        if item['type'] == 'pdf':
            cleaned_content = clean_pdf_text(item['content'])
        else:
            # For non-PDF files, just do basic cleaning
            cleaned_content = item['content'].strip()
            
        processed_item = {
            'filename': item['filename'],
            'content': cleaned_content,
            'type': item['type']
        }
        processed_content.append(processed_item)
    
    return processed_content

def get_syllabus_content(canvas, course_id: int, use_cache: bool = True) -> Optional[Dict]:
    """
    Fetch and process the syllabus content for a specific course using content export
    
    Args:
        canvas: Canvas instance
        course_id (int): The ID of the course to fetch syllabus from
        use_cache (bool): Whether to use cached data if available
        
    Returns:
        Dict: Dictionary containing processed syllabus content, or None if there's an error
    """
    try:
        # Check for cached zip file if enabled
        zip_content = None
        if use_cache:
            zip_content = get_cached_zip(course_id)
            
        if zip_content is None:
            # No cache or cache expired, need to export
            course = canvas.get_course(course_id)
            print(f"Successfully accessed course: {course.name}")
            
            print("Creating content export...")
            try:
                export = course.export_content('zip')
                print(f"Export created with ID: {export.id}")
            except Exception as e:
                print(f"Error creating export: {str(e)}")
                return None
            
            # Wait for export to complete
            print("Waiting for export to complete...")
            start_time = time.time()
            while True:
                try:
                    export = course.get_content_export(export.id)
                    elapsed_time = time.time() - start_time
                    print(f"Export status: {export.workflow_state} (Time elapsed: {elapsed_time:.1f} seconds)")
                    
                    if export.workflow_state == 'exported':
                        print(f"Export completed successfully in {elapsed_time:.1f} seconds")
                        download_url = export.attachment['url']
                        break
                    elif export.workflow_state == 'failed':
                        print(f"Export failed after {elapsed_time:.1f} seconds")
                        return None
                    elif export.workflow_state in ['created', 'exporting']:
                        print(f"Export is {export.workflow_state}...")
                    else:
                        print(f"Unknown export state: {export.workflow_state}")
                    
                    time.sleep(2)
                except Exception as e:
                    print(f"Error checking export status: {str(e)}")
                    return None
            
            # Download the zip file
            print("Downloading export file...")
            response = requests.get(download_url)
            response.raise_for_status()
            zip_content = response.content
            
            # Save to cache
            save_zip_to_cache(course_id, zip_content)
        
        # Process the zip content
        course_content = []
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_ref:
            print("\nProcessing files in export:")
            for file_name in zip_ref.namelist():
                print(f"- {file_name}")
                
                file_lower = file_name.lower()
                try:
                    if file_lower.endswith(('.txt', '.html', '.htm')):
                        with zip_ref.open(file_name) as f:
                            content = f.read().decode('utf-8')
                            course_content.append({
                                'filename': file_name,
                                'content': content,
                                'type': 'text'
                            })
                            
                    elif file_lower.endswith('.pdf'):
                        with zip_ref.open(file_name) as f:
                            pdf_reader = PyPDF2.PdfReader(io.BytesIO(f.read()))
                            text = ""
                            for page in pdf_reader.pages:
                                text += page.extract_text()
                            course_content.append({
                                'filename': file_name,
                                'content': text,
                                'type': 'pdf'
                            })
                            
                    elif file_lower.endswith('.docx'):
                        with zip_ref.open(file_name) as f:
                            doc = docx.Document(io.BytesIO(f.read()))
                            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                            course_content.append({
                                'filename': file_name,
                                'content': text,
                                'type': 'docx'
                            })
                            
                except Exception as e:
                    print(f"Error processing file {file_name}: {str(e)}")
                    continue
        
        if course_content:
            processed_content = process_course_content(course_content)
            return processed_content
        
        print("\nNo readable content found in export")
        return None
        
    except Exception as e:
        print(f"Error in get_syllabus_content: {str(e)}")
        return None

def get_announcements(canvas, course_id: int) -> Optional[List[Dict]]:
    """
    Fetch all announcements for a specific course
    
    Args:
        canvas: Canvas instance
        course_id (int): The ID of the course to fetch announcements from
        
    Returns:
        List[Dict]: List of announcement dictionaries, or None if there's an error
    """
    try:
        course = canvas.get_course(course_id)
        announcements = course.get_discussion_topics(only_announcements=True)
        
        announcements_list = []
        for announcement in announcements:
            announcement_dict = {
                'id': announcement.id,
                'title': announcement.title,
                'message': announcement.message,
                'posted_at': announcement.posted_at,
                'delayed_post_at': getattr(announcement, 'delayed_post_at', None),
                'last_reply_at': getattr(announcement, 'last_reply_at', None),
                'published': announcement.published,
                'locked': getattr(announcement, 'locked', False),
                'pinned': getattr(announcement, 'pinned', False),
                'position': getattr(announcement, 'position', None),
                'author': {
                    'id': announcement.user_id,
                    'name': getattr(announcement, 'user_name', None),
                } if hasattr(announcement, 'user_id') else None,
            }
            announcements_list.append(announcement_dict)
            
        return announcements_list
    
    except Exception as e:
        print(f"Error fetching announcements for course {course_id}: {str(e)}")
        return None

def get_module_content(canvas, course_id: int) -> Optional[List[Dict]]:
    """
    Fetch all modules and their items for a specific course
    """
    try:
        course = canvas.get_course(course_id)
        modules = course.get_modules()
        
        modules_list = []
        for module in modules:
            module_dict = {
                'id': module.id,
                'name': module.name,
                'position': module.position,
                'items': []
            }
            
            # Get all items in the module
            try:
                module_items = module.get_module_items()
                for item in module_items:
                    item_dict = {
                        'id': item.id,
                        'title': item.title,
                        'type': item.type,
                        'html_url': item.html_url,
                        'content': None
                    }
                    
                    # Handle different types of content
                    if item.type == 'Page':
                        try:
                            page = course.get_page(item.page_url)
                            item_dict['content'] = page.body
                        except:
                            print(f"Could not fetch content for page: {item.title}")
                            
                    elif item.type == 'File':
                        try:
                            # Get the file object
                            file_id = item.content_id
                            file = course.get_file(file_id)
                            
                            # Download the file if it's a PDF
                            if file.filename.lower().endswith('.pdf'):
                                print(f"Downloading PDF: {file.filename}")
                                
                                # Get the download URL
                                download_url = file.url
                                
                                # Download the PDF content
                                response = requests.get(download_url)
                                response.raise_for_status()
                                
                                # Read the PDF content
                                pdf_content = io.BytesIO(response.content)
                                pdf_reader = PyPDF2.PdfReader(pdf_content)
                                
                                # Extract text from all pages
                                text = ""
                                for page in pdf_reader.pages:
                                    text += page.extract_text()
                                
                                # Clean the extracted text
                                cleaned_text = clean_pdf_text(text)
                                item_dict['content'] = cleaned_text
                                item_dict['filename'] = file.filename
                                
                        except Exception as e:
                            print(f"Error processing PDF file {item.title}: {str(e)}")
                    
                    module_dict['items'].append(item_dict)
                    
            except Exception as e:
                print(f"Error fetching items for module {module.name}: {str(e)}")
                
            modules_list.append(module_dict)
            
        return modules_list
    
    except Exception as e:
        print(f"Error fetching modules for course {course_id}: {str(e)}")
        return None

def get_all_course_content(canvas, course_id: int) -> Dict:
    """
    Fetch all relevant content from a course including tabs, syllabus, announcements, and modules
    """
    try:
        course_content = {
            'tabs': get_course_info(canvas, course_id),
            'syllabus': get_syllabus_content(canvas, course_id),
            'announcements': get_announcements(canvas, course_id),
            'modules': get_module_content(canvas, course_id)  # Add modules content
        }
        
        # Convert datetime objects to strings before JSON serialization
        if 'syllabus' in course_content and course_content['syllabus']:
            if 'timestamp' in course_content['syllabus']:
                course_content['syllabus']['timestamp'] = course_content['syllabus']['timestamp'].isoformat()
                
        return course_content
    except Exception as e:
        print(f"Error fetching all content for course {course_id}: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    # Replace with your desired course_id
    course_id = 17700000000720596  # Remove the quotes and tilde to make it an integer
    canvas = Canvas("https://canvas.instructure.com/", os.getenv("CANVAS_API_KEY"))
    
    # Get all course content
    content = get_all_course_content(canvas, course_id)
    
    # Save to JSON file for inspection
    if content:
        with open('course_content.json', 'w') as f:
            json.dump(content, f, indent=2)
    else:
        print("Failed to fetch course content. Please check your course ID and API key.")