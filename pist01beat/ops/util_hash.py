import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Optional, Union, List

BytesLike = Union[bytes, bytearray, memoryview]
PathLike = Union[str, Path]


def sha256_bytes(data: BytesLike) -> str:
    h = hashlib.sha256()
    h.update(bytes(data))
    return h.hexdigest()


def sha256_text(text: str, encoding: str = "utf-8", errors: str = "strict") -> str:
    return sha256_bytes(text.encode(encoding, errors))


def sha256_file(path: PathLike, chunk_size: int = 1024 * 1024) -> str:
    p = Path(path)
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")

    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class HashedPath:
    relative_path: str
    sha256: str


def hash_manifest(
    paths: Sequence[PathLike],
    base_dir: Optional[PathLike] = None,
    chunk_size: int = 1024 * 1024,
) -> List[HashedPath]:
    items = []
    for p in paths:
        path = Path(p)
        items.append(HashedPath(path.as_posix(), sha256_file(path, chunk_size)))
    items.sort(key=lambda x: x.relative_path)
    return items
