from __future__ import annotations

import os
import uuid
from pathlib import Path

from werkzeug.utils import secure_filename


ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
IMAGE_SIGNATURES = {
    "image/jpeg": lambda content: content.startswith(b"\xff\xd8\xff"),
    "image/png": lambda content: content.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda content: content.startswith(b"RIFF") and content[8:12] == b"WEBP",
    "image/gif": lambda content: content.startswith((b"GIF87a", b"GIF89a")),
}


class LocalStorageAdapter:
    """Local object-storage simulation; swap this adapter for Firebase/S3 in deployment."""

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, user_id: str, file_storage) -> dict[str, str | int]:
        if not file_storage or not file_storage.filename:
            raise ValueError("Choose an image file to upload.")
        content_type = file_storage.content_type or ""
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Only JPEG, PNG, WEBP, or GIF profile images are supported.")
        stream = file_storage.stream
        current_position = stream.tell()
        header = stream.read(16)
        stream.seek(current_position)
        if not IMAGE_SIGNATURES[content_type](header):
            raise ValueError("The uploaded file does not match its declared image type.")
        safe_name = secure_filename(file_storage.filename) or "profile-image"
        object_id = uuid.uuid4().hex
        relative_key = f"{user_id}/profile/{object_id}-{safe_name}"
        destination = self.root / relative_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        file_storage.save(destination)
        size = os.path.getsize(destination)
        if size > 3 * 1024 * 1024:
            destination.unlink(missing_ok=True)
            raise ValueError("Profile images must be 3 MB or smaller.")
        return {"object_key": relative_key, "filename": safe_name, "content_type": content_type, "size_bytes": size}

    def path_for(self, object_key: str) -> Path:
        candidate = (self.root / object_key).resolve()
        if self.root.resolve() not in candidate.parents:
            raise ValueError("Invalid storage key.")
        return candidate
