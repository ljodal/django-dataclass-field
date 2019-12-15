import dataclasses
from typing import List


@dataclasses.dataclass
class Artist:

    name: str


@dataclasses.dataclass
class Album:

    name: str
    artist: Artist


@dataclasses.dataclass
class SongWithAlbum:

    name: str
    album: Album


@dataclasses.dataclass
class SongWithAlbumName:
    name: str
    album_name: str


@dataclasses.dataclass
class SongWithLikes:
    name: str

    # Field with default
    like_count: int = 0

    # Field with default_factory
    liked_by: List[str] = dataclasses.field(default_factory=list)
