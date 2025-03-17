from canvasapi import Canvas
from dotenv import load_dotenv
import os
import json
from getCourses import get_all_courses, get_current_courses, save_courses_to_json
from getAssignments import get_course_assignments
from datetime import datetime
import pytz

def initialize_canvas():
    """Initialize and return a Canvas instance"""
    load_dotenv("secrets.env")
    API_URL = "https://canvas.instructure.com/"
    API_KEY = os.getenv("CANVAS_API_KEY")
    return Canvas(API_URL, API_KEY)

def get_current_courses_assignments():
    """
    Get assignments for all current courses and save them to a JSON file
    """
    try:
        # Initialize Canvas and get current courses
        canvas = initialize_canvas()
        all_courses = get_all_courses(canvas)
        current_courses = get_current_courses(all_courses)
        
        # Save courses to JSON files
        save_courses_to_json(all_courses, "AllCourses.json")
        save_courses_to_json(current_courses, "CurrentCourses.json")
        
        # Get assignments for each current course
        all_assignments = {}
        for course in current_courses:
            course_id = course['id']
            course_name = course['name']
            print(f"\nFetching assignments for: {course_name}")
            
            assignments = get_course_assignments(canvas, course_id)
            if assignments:
                all_assignments[course_name] = assignments
            else:
                print(f"Failed to fetch assignments for {course_name}")
        
        # Save all assignments to a single file
        if all_assignments:
            with open("AllAssignments.json", "w") as f:
                json.dump(all_assignments, f, indent=2)
            print("\nSuccessfully fetched and saved all assignments!")
        else:
            print("\nNo assignments were successfully fetched.")
            
        return all_assignments
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def display_future_assignments(all_assignments):
    """
    Display assignments that are due in the future from the provided assignments dictionary
    
    Args:
        all_assignments (dict): Dictionary containing courses and their assignments
    """
    # Get current time in UTC
    current_time = datetime.now(pytz.UTC)
    
    print("\nUpcoming Assignments:")
    print("-" * 50)
    
    for course_name, assignments in all_assignments.items():
        future_assignments = []
        for assignment in assignments:
            # Check if due_at exists and is not None
            if assignment.get('due_at'):
                due_date = datetime.strptime(assignment['due_at'], "%Y-%m-%dT%H:%M:%SZ")
                due_date = pytz.UTC.localize(due_date)
                
                if due_date > current_time:
                    future_assignments.append({
                        'name': assignment['name'],
                        'due_date': due_date.strftime("%Y-%m-%d %H:%M UTC")
                    })
        
        if future_assignments:
            print(f"\n{course_name}:")
            for assignment in future_assignments:
                print(f"  - {assignment['name']} (Due: {assignment['due_date']}")

def main():
    """
    Main function to run the program
    """
    print("Starting Canvas Data Collection...")
    assignments = get_current_courses_assignments()
    
    if assignments:
        print("\nProgram completed successfully!")
        display_future_assignments(assignments)
    else:
        print("\nProgram encountered an error.")

if __name__ == "__main__":
    main() 