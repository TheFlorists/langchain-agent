from canvasapi import Canvas
from dotenv import load_dotenv
import os
import json
load_dotenv("secrets.env")

def get_course_assignments(canvas, course_id):
    """
    Get assignments for a specific course
    Args:
        canvas: Canvas instance
        course_id: ID of the course to get assignments for
    Returns:
        List of assignment dictionaries or None if there's an error
    """
    try:
        # Get the specific course
        course = canvas.get_course(course_id)
        
        # Get all assignments for the course
        assignments = list(course.get_assignments())
        
        # Convert assignments to serializable dictionaries
        assignment_list = []
        essential_fields = {
            'id', 'name', 'description', 'points_possible', 
            'due_at', 'unlock_at', 'lock_at', 'course_id',
            'workflow_state', 'submission_types', 'grading_type'
        }
        
        for assignment in assignments:
            assignment_dict = {}
            for key, value in assignment.__dict__.items():
                if key not in essential_fields:
                    continue
                try:
                    # Handle datetime objects
                    if hasattr(value, 'isoformat') and callable(value.isoformat):
                        assignment_dict[key] = value.isoformat()
                    else:
                        # Test if the value is JSON serializable
                        json.dumps({key: value})
                        assignment_dict[key] = value
                except (TypeError, OverflowError):
                    pass
            assignment_list.append(assignment_dict)
        
        print(f"Found {len(assignment_list)} assignments for course {course.name}")
        return assignment_list

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    # Replace with your desired course_id
    course_id = "17700000000720596"
    canvas = Canvas("https://canvas.instructure.com/", os.getenv("CANVAS_API_KEY"))
    assignments = get_course_assignments(canvas, course_id)
