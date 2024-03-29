import asyncio
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor

import aiosqlite

# TODO: Consider use more sustainable way to handle async
CHUNK_SIZE = 5 * 1024 * 1024
DB_NAME = "metadata.db"
file_directory = "files/"


def get_path_sync(identifier, is_id):
    """Synchronously wrapper function to get file path for given identifier."""

    async def get_path_async(identifier, is_id):
        if is_id:
            query = "SELECT path FROM metadata WHERE id = ?"
        else:
            query = "SELECT path FROM metadata WHERE filename = ?"
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(query, (identifier,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                return None

    with ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, get_path_async(identifier, is_id))
        return future.result()


def generate_file_stream(path):
    """Generate a file stream from the given path."""
    if os.path.isdir(path):
        for filename in sorted(os.listdir(path)):
            chunk_path = os.path.join(path, filename)
            with open(chunk_path, "rb") as file:
                while chunk := file.read(CHUNK_SIZE):
                    yield chunk
    else:
        with open(path, "rb") as file:
            while chunk := file.read(CHUNK_SIZE):
                yield chunk


def verify_checksum(file_path, expected_checksum):
    return calculate_checksum(file_path) == expected_checksum


def calculate_checksum(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
