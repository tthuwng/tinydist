from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
npz_directory = "./npz/"

DB_SERVER_URL = "http://localhost:5002/metadata/upload"


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400
    if file and file.filename.endswith(".npz"):
        file_path = os.path.join(npz_directory, file.filename)
        file.save(file_path)
        data = {
            "filename": file.filename,
            "file_path": file_path,
            "category": "default",
        }
        response = requests.post(DB_SERVER_URL, json=data)
        return response.json()
    else:
        return jsonify({"message": "Invalid file format"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5001, host="0.0.0.0")
