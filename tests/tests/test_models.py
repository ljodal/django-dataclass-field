import pytest
from django.db.models import F

from dataclass_field import DataclassField, JSONObject

from ..models import Album, Song
from ..types import Artist, SongWithAlbum


@pytest.mark.usefixtures("db")
def test_create_model():
    """
    Test that we can create a model with a dataclass instance.
    """

    album = Album.objects.create(
        name="Ompa til du dør", artist=Artist(name="Kaizers Orchestra")
    )
    assert album.id is not None
    assert album.name == "Ompa til du dør"
    assert isinstance(album.artist, Artist)
    assert album.artist.name == "Kaizers Orchestra"

    # Load from the database and make sure it still works
    album = Album.objects.get()
    assert album.id is not None
    assert album.name == "Ompa til du dør"
    assert isinstance(album.artist, Artist)
    assert album.artist.name == "Kaizers Orchestra"


@pytest.mark.usefixtures("db")
def test_useage_as_annotation():
    """
    Test that the field can be used as an annotation.
    """

    album = Album.objects.create(
        name="Ompa til du dør", artist=Artist(name="Kaizers Orchestra")
    )
    Song.objects.create(album=album, name="Ompa til du dør")

    instance = Song.objects.values_list(
        JSONObject(
            name=F("name"),
            album=JSONObject(name=F("album__name"), artist=F("album__artist"),),
            output_field=DataclassField(SongWithAlbum),
        ),
        flat=True,
    ).get()

    assert isinstance(instance, SongWithAlbum)
