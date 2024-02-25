# tinydist

a distributed system for managing and processing various types of files (including training target and model) into a single flask server. It's designed to streamline the handling of files by providing a structured way to upload, list, and access these files and their metadata through a set of RESTful APIs. Goal is to make it ideal for machine learning data pipelines of handling of training targets.

## Features

- File upload with optional categorization.
- Chunked file upload for large files.
- Listing of uploaded files with metadata.
- Downloading files by ID or filename.
- Deletion of files and associated metadata.

## Setup

1. Clone & Install dependencies:

```
pip install -r requirements.txt
pip install -e .
```

2. Set environment variables (optionally, use a `.env` file with `python-dotenv`):

- `AUTH_TOKEN`: A token for simple API authentication.
- `SERVER_URL`: The URL where the server is accessible (for testing or production).

3. Run the server:

```
make server

make test # run all tests
```

### API

- POST /upload: Uploads file, saved in a specified directory, its metadata is created.

```
curl -F "file=@path_to_file.any_extension" -F "category=optional_category" -H "Authorization: secret_token" http://host_name:5002/upload
```

- GET /metadata/list: Lists metadata for files. Optionally, specify limit for the number of records and category to filter by file category.

```
curl -G -H "Authorization: secret_token" http://hostname:5002/metadata/list
```

- GET /files: Download a single file or multiple files (as a ZIP). Specify file IDs as query parameters.

```
curl -H "Authorization: secret_token" -o "downloaded_filename.extension" http://hostname:5002/files?id=1?id=2
```

- DELETE /delete: Delete metadata and move the associated file to trash directory. If the file doesn't exist, deletes the metadata. If the metadata doesn't exist but a file with the corresponding name is found, it moves this file to the trash.

```
curl -X DELETE "http://localhost:5002/delete?id=123" -H "Authorization: secret_token" # by metadata id

curl -X DELETE "http://localhost:5002/delete?filename=example.txt" -H "Authorization: secret_token" # by filename

```

### Environment Configuration & Auth

Set AUTH_TOKEN in your environment to secure the API endpoints.

.env File Example:

```
AUTH_TOKEN=secret_token
```

This server uses a simple token-based authentication method. Include an Authorization header with your requests to authenticate:

```
-H "Authorization: secret_token"
```

## Contributing

Contributions to tinydist are welcome! Please consider forking the repository, making your changes, and submitting a pull request.
