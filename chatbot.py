import os
import threading
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from rapidfuzz import process, fuzz

# Flask app
app = Flask(__name__)

# 🔹 Load Google Sheets Data
SERVICE_ACCOUNT_FILE = "service-account-key.json"  # Update this path
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

# Google Sheets details
SHEET_ID = "https://docs.google.com/spreadsheets/d/1JOODvFUmvrHFm2Z-3hTOuB4SIwUpDplLcenEHKQDgz0/edit?gid=0#gid=0" 
RANGE_NAME = "Sheet1!A:B"

def fetch_faq_data():
    """Fetch FAQ data from Google Sheets."""
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])
    return values[1:] if values else []  # Skip headers

faq_data = fetch_faq_data()

def get_best_match(query, questions, threshold=80):
    """Find the best matching question."""
    match = process.extractOne(query, questions, scorer=fuzz.ratio)
    if match and match[1] >= threshold:
        return match[0]
    return None

@app.route("/ask", methods=["POST"])
def ask_bot():
    """Receive user query and return the best-matching answer."""
    user_query = request.json.get("query", "").strip()
    if not user_query:
        return jsonify({"response": "Please provide a valid question."})

    questions = [row[0] for row in faq_data]
    match = get_best_match(user_query, questions)

    if match:
        response = faq_data[questions.index(match)][1]
    else:
        response = "I'm sorry, I couldn't find an answer to your question."

    return jsonify({"response": response})

# Run Flask server in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
