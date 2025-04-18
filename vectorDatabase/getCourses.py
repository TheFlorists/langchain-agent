from canvasapi import Canvas
from dotenv import load_dotenv
import os
import json

def get_all_courses(canvas):
    """Get all courses for the current user"""
    user = canvas.get_user('self')
    print(f"logged in as: {user.name}")

    courses = list(user.get_courses(completed=False))
    dict_courses = []
    
    for course in courses:
        course_dict = {}
        for key, value in course.__dict__.items():
            try:
                # Handle datetime objects by converting them to ISO format strings
                if hasattr(value, 'isoformat') and callable(value.isoformat):
                    course_dict[key] = value.isoformat()
                else:
                    # Test if the value is JSON serializable
                    json.dumps({key: value})
                    course_dict[key] = value
            except (TypeError, OverflowError) as e:
                # Skip attributes that can't be serialized
                # print(f"Error: {e}, {key}")
                pass
        dict_courses.append(course_dict)
    
    print(f"Found {len(dict_courses)} total courses")
    return dict_courses

def get_current_courses(courses):
    """Filter and return current courses for WN 2025"""
    current_courses = []
    for course in courses:
        if "access_restricted_by_date" in course and course["access_restricted_by_date"]:
            continue
        # print(f"{course['name']}", end=" ")
        _course = course['name'].split(" ")
        course_name, course_misc, course_term = _course[:2], _course[2:-2], _course[-2:]
        if ' '.join(course_term) == "WN 2025":
            current_courses.append(course)
            print(f"{course_name} {course_term}")
    return current_courses

def save_courses_to_json(courses, filename):
    """Save courses to a JSON file"""
    with open(filename, "w") as f:
        json.dump(courses, f, indent=2)