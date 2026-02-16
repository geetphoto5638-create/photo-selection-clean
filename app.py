from flask import Flask, request, render_template, redirect
import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread

app = Flask(__name__)

# ---------------- GOOGLE CREDS ----------------
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# Render environment variable support
if "GOOGLE_CREDS_JSON" in os.environ:
    creds_info = json.loads(os.environ["GOOGLE_CREDS_JSON"])
else:
    with open("credentials.json", "r", encoding="utf-8") as f:
        creds_info = json.load(f)

CREDS = Credentials.from_service_account_info(
    creds_info,
    scopes=SCOPES
)

drive = build("drive", "v3", credentials=CREDS)

# Google Sheet Connect
gc = gspread.authorize(CREDS)
sheet = gc.open_by_key("1WQ2YsFnxgD7UVxtn2MWFKD0dOtDaLpAqu32hEy7hj7U").sheet1

# ----------- YOUR MAIN FOLDER ID ----------
MAIN_FOLDER_ID = "1Fu10oB_TpUZxGMTmrFs5tq4lEbBd9DSa"


# ---------------- CLIENT PAGE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        client = request.form.get("client")
        return redirect(f"/viewer?client={client}")

    return '''
        <h2>Enter Client Name</h2>
        <form method="post">
            <input type="text" name="client" required>
            <button type="submit">Open Photos</button>
        </form>
    '''


# ---------------- VIEWER ----------------
@app.route("/viewer")
def viewer():
    client = request.args.get("client")

    query = f"'{MAIN_FOLDER_ID}' in parents and mimeType contains 'image/' and trashed=false"

    results = drive.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])

    # Add numbering
    for i, file in enumerate(files, start=1):
        file["number"] = i

    return render_template("viewer.html", files=files, client=client)


# ---------------- SAVE ----------------
@app.route("/save", methods=["POST"])
def save():
    client = request.form.get("client")
    selected_photos = request.form.getlist("photos")

    if not client:
        return "Client missing", 400

    for photo in selected_photos:
        sheet.append_row([client, photo, "Selected"])

    return "Saved to Google Sheet Successfully"


# --------- Render Required PORT ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
