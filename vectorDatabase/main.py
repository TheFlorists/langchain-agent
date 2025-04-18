from canvasapi import Canvas
from dotenv import load_dotenv
import os
import json
from getCourses import get_all_courses, get_current_courses, save_courses_to_json
from getAssignments import get_course_assignments
from getQuizes import get_course_quizzes
from datetime import datetime
import pytz

class CanvasManager:
    def __init__(self):
        """Initialize the CanvasManager with Canvas instance and course data"""
        self.canvas = self._initialize_canvas()
        self.all_courses = get_all_courses(self.canvas)
        self.current_courses = get_current_courses(self.all_courses)
        
        # Save courses to JSON files
        save_courses_to_json(self.all_courses, "AllCourses.json")
        save_courses_to_json(self.current_courses, "CurrentCourses.json")

    def _initialize_canvas(self):
        """Initialize and return a Canvas instance"""
        load_dotenv("secrets.env")
        API_URL = "https://canvas.instructure.com/"
        API_KEY = os.getenv("CANVAS_API_KEY")
        return Canvas(API_URL, API_KEY)

    def get_current_courses_assignments(self):
        """Get assignments for all current courses and save them to a JSON file"""
        try:
            all_assignments = {}
            for course in self.current_courses:
                course_id = course['id']
                course_name = course['name']
                print(f"\nFetching assignments for: {course_name}")
                
                assignments = get_course_assignments(self.canvas, course_id)
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

    def get_current_courses_quizzes(self):
        """Get quizzes for all current courses and save them to a JSON file"""
        try:
            all_quizzes = {}
            for course in self.current_courses:
                course_id = course['id']
                course_name = course['name']
                print(f"\nFetching quizzes for: {course_name}")
                
                quizzes = get_course_quizzes(self.canvas, course_id)
                if quizzes:
                    all_quizzes[course_name] = quizzes
            
            # Save all quizzes to a single file
            if all_quizzes:
                with open("AllQuizzes.json", "w") as f:
                    json.dump(all_quizzes, f, indent=2)
                print("\nSuccessfully fetched and saved all quizzes!")
            else:
                print("\nNo quizzes were successfully fetched.")
                
            return all_quizzes
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def display_future_assignments(self, all_assignments):
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
                    print(f"  - {assignment['name']} (Due: {assignment['due_date']})")

    def display_all_quizzes(self, all_quizzes):
        """
        Display all quizzes from the provided quizzes dictionary
        
        Args:
            all_quizzes (dict): Dictionary containing courses and their quizzes
        """
        print("\nAll Quizzes:")
        print("-" * 50)
        
        for course_name, quizzes in all_quizzes.items():
            if quizzes:  # Only print course name if it has quizzes
                print(f"\n{course_name}:")
                for quiz in quizzes:
                    due_date_str = "No due date"
                    if quiz.get('due_at'):
                        due_date = datetime.strptime(quiz['due_at'], "%Y-%m-%dT%H:%M:%SZ")
                        due_date = pytz.UTC.localize(due_date)
                        due_date_str = due_date.strftime("%Y-%m-%d %H:%M UTC")
                    
                    print(f"  - {quiz['title']} (Due: {due_date_str})")

def main():
    """Main function to run the program"""
    print("Starting Canvas Data Collection...")
    
    # Create single instance of CanvasManager
    canvas_manager = CanvasManager()
    
    # Fetch assignments and quizzes using the manager
    assignments = canvas_manager.get_current_courses_assignments()
    # quizzes = canvas_manager.get_current_courses_quizzes()
    
    if assignments: # assignments or quizzes
        print("\nProgram completed successfully!")
        if assignments:
            canvas_manager.display_future_assignments(assignments)
        # if quizzes:
        #     canvas_manager.display_all_quizzes(quizzes)
    else:
        print("\nProgram encountered an error.")

if __name__ == "__main__":
    main() 