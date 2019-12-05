import dataclasses


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
