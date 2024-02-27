import io
import json
import os

import dotenv

dotenv.load_dotenv()

AUTH_TOKEN = os.getenv("AUTH_TOKEN")


def test_list_metadata(client):
    """Test the metadata listing endpoint."""
    response = client.get("/metadata/list", headers={"Authorization": AUTH_TOKEN})
    assert response.status_code == 200
    data = json.loads(response.data.decode("utf-8"))
    assert isinstance(data, list)


def test_upload_file(client):
    """Test the file upload endpoint."""
    data = {"file": (io.BytesIO(b"Hello World"), "hello.txt"), "category": "default"}
    response = client.post(
        "/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": AUTH_TOKEN},
    )
    assert response.status_code == 200
    response_data = json.loads(response.data.decode("utf-8"))
    assert "File uploaded successfully" in response_data["message"]


def upload_dummy_file(
    client, filename="test.txt", content=b"Hello, World!", category="default"
):
    data = {"file": (io.BytesIO(content), filename), "category": category}
    return client.post(
        "/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": AUTH_TOKEN},
    )


def test_upload_small_file(client):
    response = upload_dummy_file(
        client, filename="small.txt", content=b"Small file content"
    )
    assert response.status_code == 200
    data = json.loads(response.data.decode("utf-8"))
    assert "uploaded successfully" in data["message"]


def test_upload_large_file(client):
    large_content = b"a" * (5 * 1024 * 1024 + 1)  # Just over 5 MB
    response = upload_dummy_file(client, filename="large.txt", content=large_content)
    assert response.status_code == 200
    data = json.loads(response.data.decode("utf-8"))
    assert "uploaded successfully" in data["message"]


# TODO: add test get small & big files
# def test_get_small_file(client):
#     filename = "small_test_file.txt"
#     file_content = b"Small file content"
#     response = upload_dummy_file(client, filename=filename, content=file_content)
#     assert response.status_code == 200

#     download_response = client.get(f'/get?filename={filename}')
#     assert download_response.status_code == 200
#     assert download_response.data == file_content
