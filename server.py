from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

DB_SERVER_METADATA_LIST_URL = "http://localhost:5002/metadata/list"
DB_SERVER_FILE_URL = "http://localhost:5002/file/"


@app.route("/process", methods=["GET"])
def process_files():
    top_x = request.args.get("top", default=5, type=int)
    response = requests.get(DB_SERVER_METADATA_LIST_URL)
    if response.status_code == 200:
        files_metadata = response.json()
        processed_files = files_metadata[:top_x]
        return jsonify({"data": processed_files})
    else:
        return jsonify({"message": "Failed to retrieve files metadata"}), 500


@app.route("/file/<int:file_id>", methods=["GET"])
def get_file(file_id):
    file_url = f"{DB_SERVER_FILE_URL}{file_id}"
    return requests.get(file_url).content, {"Content-Type": "application/octet-stream"}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
