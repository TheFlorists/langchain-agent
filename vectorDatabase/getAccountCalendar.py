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

    # Get calendar events directly for the user
    calendar_events = canvas.get_calendar_events(
        type='event',
        start_date='2024-01-01',  # Add appropriate date range
        end_date='2025-12-31',    # Add appropriate date range
        context_codes=['user_'+str(user.id), 'course_17700000000720596']  # Specify context codes
    )
    
    # Process the calendar events as needed
    for event in calendar_events:
        print(f"Event: {event.title}")

except Exception as e:
    print(f"Error: {str(e)}")