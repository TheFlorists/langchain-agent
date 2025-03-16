from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os
from typing import List
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI()
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


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

    # set up tools
    config = types.GenerateContentConfig(
        tools=[
            say_hello_world,
        ])

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=formatted_history,
            config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {str(e)}")

    return {"message": response.text}


def say_hello_world():
    """Say hello world back to the user if the user asks for it

    Args:
        no args

    Returns:
        a string saying hello world
    """
    return 'hello world tool call TEST'

