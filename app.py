from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os
from typing import List
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import logging

app = FastAPI()
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Add logging configuration at the start of your file
logging.basicConfig(level=logging.DEBUG)

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


# format for a message
class ChatTurn(BaseModel):
    role: str # user OR assistant
    content: str

### REQUIRED FORMAT FOR SENDING REQUEST
class ChatRequest(BaseModel):
    history: List[ChatTurn]

# Format chat history for Gemini api
def format_message(turn: ChatTurn) -> dict:
    return {
        "role": turn.role,
        "parts": [
            {
                "text": turn.content,
            }
        ]
    }

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    if not chat_request.history:
        raise HTTPException(status_code=400, detail="Chat history is empty.")
    
    formatted_history = [format_message(turn) for turn in chat_request.history]
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Set up tools
    config = types.GenerateContentConfig(
        tools=[
            {
                "function_declarations": [
                    {
                        "name": "create_calendar_event",
                        "description": "Create a new event in Google Calendar",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Title of the event"
                                },
                                "start_time": {
                                    "type": "string", 
                                    "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                                },
                                "end_time": {
                                    "type": "string",
                                    "description": "End time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Optional description for the event"
                                }
                            },
                            "required": ["title", "start_time", "end_time"]
                        }
                    }
                ]
            }
        ]
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=formatted_history,
            config=config
        )
        
        # Log the response for debugging
        logging.debug(f"Gemini API response: {response}")
        
        # Handle function calling if present
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        function_call = part.function_call
                        if function_call and function_call.name == "create_calendar_event":
                            # Extract arguments
                            args = function_call.args
                            # Call the function
                            result = create_calendar_event(
                                title=args.get("title"),
                                start_time=args.get("start_time"),
                                end_time=args.get("end_time"),
                                description=args.get("description")
                            )
                            # Return the result
                            return {"message": str(result)}
        
        # If no function call, return the standard response
        return {"message": response.text}
        
    except Exception as e:
        logging.error(f"Error processing Gemini API response: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {str(e)}")


def say_hello_world():
    """Say hello world back to the user if the user asks for it

    Args:
        no args

    Returns:
        a string saying hello world
    """
    return 'hello world tool call TEST'

def create_calendar_event(title: str, start_time: str, end_time: str, description: str = None):
    """
    Create a new event in Google Calendar
    
    Args:
        title: Title of the event
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Optional description for the event
        
    Returns:
        A dictionary with the event details or an error message
    """
    SERVICE_ACCOUNT_FILE = 'service_account_key.json'
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    try:
        # Load credentials from your service account file
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )
        
        # Build the service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Create event details
        event = {
            'summary': title,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            }
        }
        
        if description:
            event['description'] = description
            
        # Insert the event
        event = service.events().insert(calendarId='primary', body=event).execute()
        
        return {
            'status': 'success',
            'event_id': event.get('id'),
            'link': event.get('htmlLink')
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }