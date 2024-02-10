# tinydist

a distributed system for managing and processing various types of files (including training target and model) into a single flask server. It's designed to streamline the handling of files by providing a structured way to upload, list, and access these files and their metadata through a set of RESTful APIs. Goal is to make it ideal for machine learning data pipelines of handling of training targets.

### API

- POST /upload: Uploads an .npz file. The file is saved in a specified directory, and its metadata is uploaded to the DB server.

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

### Start Servers (default localhost)

```
python app_server.py
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
