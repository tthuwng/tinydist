# tinydist

a distributed system for managing and processing `.npz` training target files across 3 separate services: a Node server, a central processing server, and a db server. It's designed to streamline the handling of files by providing a structured way to upload, list, and access these files and their metadata through a set of RESTful APIs. Goal is to make it ideal for machine learning data pipelines of handling of training targets.

### API

Node Server

- POST /upload: Uploads an .npz file. The file is saved in a specified directory, and its metadata is uploaded to the DB server.

Processing Server

- GET /process: Fetches the top x latest .npz files' metadata from the DB server and processes them. The number x can be specified as a query parameter.
- GET /file/<int:file_id>: Streams the content of a specific .npz file by its ID from the DB server.

DB Server

- POST /metadata/upload: Receives and stores metadata for uploaded .npz files.
- GET /metadata/list: Returns a list of all .npz files' metadata.
- GET /file/<int:file_id>: Serves the actual .npz file content based on its database ID.

### Start Servers (default localhost)

```
# this is just nginx under the hood
python db_server.py # default port 5002
python node.py # default port 5001
python server.py # default port 5000
```

### Usage

- Use a tool like curl or Postman to POST an .npz file to the Node server's /upload endpoint.

```
curl -F "file=@path_to_your_file.npz" http://localhost:5001/upload
```
