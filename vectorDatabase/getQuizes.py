from typing import List, Dict, Optional

def get_course_quizzes(canvas, course_id: int) -> Optional[List[Dict]]:
    """
    Fetch all quizzes for a specific course
    
    Args:
        canvas: Canvas instance
        course_id (int): The ID of the course to fetch quizzes from
        
    Returns:
        List[Dict]: List of quiz dictionaries, or None if there's an error
    """
    try:
        course = canvas.get_course(course_id)
        quizzes = course.get_quizzes()
        print(quizzes[0])
        
        # Convert quiz objects to dictionaries with relevant information
        quiz_list = []
        for quiz in quizzes:
            quiz_dict = {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'due_at': quiz.due_at,
                'points_possible': quiz.points_possible,
                'quiz_type': quiz.quiz_type,
                'allowed_attempts': quiz.allowed_attempts
            }
            quiz_list.append(quiz_dict)
            
        return quiz_list
    
    except Exception as e:
        print(f"Error fetching quizzes for course {course_id}: {str(e)}")
        return None
