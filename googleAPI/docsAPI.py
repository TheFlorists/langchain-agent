import datetime as dt
import os
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import os.path
SCOPES = ['https://www.googleapis.com/auth/drive']

def authorize():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
   
def doc_id(title):
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', [SCOPES, 'https://www.googleapis.com/auth/documents'])
        
        drive_service = build('drive', 'v3', credentials=creds)

        doc_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document'
        }
        drive_service = build('drive', 'v3', credentials=creds)
        doc = drive_service.files().create(body=doc_metadata).execute()
        id = doc['id']
        return id

def doc_content(message, id):
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', [SCOPES, 'https://www.googleapis.com/auth/documents'])
        
        doc_service = build('docs', 'v1', credentials=creds)

        time = dt.datetime.now()
        time = time.time()
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': f"{time} - {message}\n"
                }
            }
        ]
        result = doc_service.documents().batchUpdate(documentId=id, body={'requests': requests}).execute()
        return result

def doc_download(id, saved_folder, title):
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', [SCOPES, 'https://www.googleapis.com/auth/documents'])

        export_url = f"https://www.googleapis.com/drive/v3/files/{id}/export?mimeType=application/pdf"
       
        headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(export_url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Unable to download document (status code {response.status_code})")
        return

    # Checks if folder exists, create if not
    if not os.path.exists(saved_folder):
        os.makedirs(saved_folder)

    # File name
    file_name = os.path.join(saved_folder, f"{title}.pdf")

    with open(file_name, "wb") as pdf_file:
        pdf_file.write(response.content)

    print(f"Document successfully downloaded as {file_name}")

def main():
    authorize()
    title = 'Test document'
    message = 'This is a test message'
    id = doc_id(title)
    doc_content(message, id)


    saved_folder = "downloads" # Change this folder for specific download location
    doc_download(id, saved_folder, title) 

if __name__ == '__main__':
    main()