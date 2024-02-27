import os
import tempfile
from urllib.parse import unquote

import click
import dotenv
import requests
from tqdm import tqdm

from tinydist.utils import CHUNK_SIZE, calculate_checksum

dotenv.load_dotenv()

SERVER_URL = os.getenv("SERVER_URL")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")


def chunk_file(file_path, chunk_size=CHUNK_SIZE):
    """
    Generator to read a file in chunks.
    """
    with open(file_path, "rb") as f:
        chunk = f.read(chunk_size)
        while chunk:
            yield chunk
            chunk = f.read(chunk_size)


def upload_file_chunk(
    file_path, filename, total_chunks, chunk_index, category, checksum=None
):
    """
    Uploads a single chunk of a file to the server.
    """
    url = f"{SERVER_URL}{'upload' if total_chunks == 1 else 'upload_chunk'}"
    headers = {"Authorization": AUTH_TOKEN}
    data = {
        "filename": filename,
        "chunkIndex": chunk_index,
        "totalChunks": total_chunks,
        "category": category,
        "totalChunks": total_chunks,
        "checksum": checksum,
    }
    with open(file_path, "rb") as f:
        files = {"file": (filename, f, "application/octet-stream")}
        response = requests.post(url, headers=headers, data=data, files=files)
    return response


def upload_file(file_path, category):
    """
    Handles upload a file, automatically chunking and uploading as necessary.
    """
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    total_chunks = max(
        (file_size // CHUNK_SIZE) + (1 if file_size % CHUNK_SIZE else 0), 1
    )

    if file_size <= CHUNK_SIZE:
        with tqdm(total=1, desc=f"Uploading {filename}", unit="file") as pbar:
            upload_file_chunk(file_path, filename, 1, 0, category)
            pbar.update()
    else:
        with tqdm(
            total=total_chunks, desc=f"Uploading {filename}", unit="chunk"
        ) as pbar:
            for i, chunk in enumerate(chunk_file(file_path)):
                chunk_path = f"{file_path}.part{i}"
                with open(chunk_path, "wb") as temp_chunk_file:
                    temp_chunk_file.write(chunk)
                upload_file_chunk(
                    chunk_path,
                    filename,
                    total_chunks,
                    i,
                    category,
                    checksum=calculate_checksum(file_path),
                )
                pbar.update()
                os.remove(chunk_path)  # Clean up the temporary chunk file
    click.echo(f"{filename} uploaded successfully.")


@click.group()
def cli():
    """TinyDist CLI tool."""
    pass


@cli.command()
@click.option("--category", default="default", help="Category for the uploaded files.")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def upload(paths, category):
    """Upload a file or all files in a folder."""

    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for name in files:
                    upload_file(os.path.join(root, name), category)
        elif os.path.isfile(path):
            upload_file(path, category)
        else:
            click.echo("Path does not exist.")


def safe_filename(disposition, default="downloaded_file"):
    """Extract filename safely from Content-Disposition or use a default."""
    if disposition:
        parts = disposition.split("filename=")
        if len(parts) > 1:
            return unquote(parts[1].strip("\"' "))
    return default


def assemble_chunks(file_name, total_chunks, temp_dir):
    """Assemble chunks into the original file."""
    with open(file_name, "wb") as assembled_file:
        for i in range(total_chunks):
            chunk_name = os.path.join(temp_dir, f"{file_name}.part{i}")
            with open(chunk_name, "rb") as chunk_file:
                assembled_file.write(chunk_file.read())


@cli.command()
@click.argument("file_ids", nargs=-1)
def get(file_ids):
    """Download files or chunks and reassemble if necessary."""
    for file_id in file_ids:
        response = requests.get(
            f"{SERVER_URL}get?id={file_id}",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            stream=True,
        )
        content_disp = response.headers.get("Content-Disposition", "")
        file_name = safe_filename(content_disp, f"downloaded_{file_id}")

        if "X-Chunked" in response.headers:
            with tempfile.TemporaryDirectory() as temp_dir:
                total_chunks = 0
                with tqdm(
                    desc=f"Downloading {file_name}",
                    unit="B",
                    unit_scale=True,
                    total=int(response.headers.get("Content-Length", 0)),
                ) as bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        chunk_path = os.path.join(
                            temp_dir, f"{file_name}.part{total_chunks}"
                        )
                        with open(chunk_path, "wb") as chunk_file:
                            chunk_file.write(chunk)
                        total_chunks += 1
                        bar.update(len(chunk))
                assemble_chunks(file_name, total_chunks, temp_dir)

        else:
            with open(file_name, "wb") as f_out, tqdm(
                desc=f"Downloading {file_name}",
                unit="B",
                unit_scale=True,
                total=int(response.headers.get("Content-Length", 0)),
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    f_out.write(chunk)
                    bar.update(len(chunk))
        assembled_checksum = calculate_checksum(file_name)
        response = requests.post(
            f"{SERVER_URL}verify_get?filename={file_name}",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            data={"filename": file_name, "checksum": assembled_checksum},
        )
        if response.status_code == 200:
            print(f"File downloaded and verified successfully: {file_name}")
        else:
            print(f"File download failed: {file_name}")


if __name__ == "__main__":
    cli()
