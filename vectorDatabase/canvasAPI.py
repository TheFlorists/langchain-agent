# Import the Canvas class
from canvasapi import Canvas
from dotenv import load_dotenv
import os
import json
load_dotenv("secrets.env")

# Canvas API URL
API_URL = "https://canvas.instructure.com/"
API_KEY = os.getenv("CANVAS_API_KEY")

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

try:
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
    
    print(f"Found {len(dict_courses)} courses")

    with open("courses.json", "w") as f:
        json.dump(dict_courses, f, indent=2)

    for course in dict_courses:
        if "access_restricted_by_date" in course and course["access_restricted_by_date"]:
            continue
        # print(f"{course['name']}", end=" ")
        course = course['name'].split(" ")
        course_name, course_misc, course_term = course[:2], course[2:-2], course[-2:]

        print(f"{course_name} {course_term}")

except Exception as e:
    print(f"Error: {str(e)}")