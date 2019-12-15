import pytest
from django.contrib.postgres.fields import ArrayField
from django.db.models import F, IntegerField, TextField, Value

from dataclass_field import DataclassField, JSONObject

from ..models import Album, Song
from ..types import Artist, SongWithAlbum, SongWithAlbumName, SongWithLikes


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


@pytest.mark.usefixtures("db")
def test_dataclasses_queryset():
    """
    Test that the field can be used as an annotation.
    """

    album = Album.objects.create(
        name="Ompa til du dør", artist=Artist(name="Kaizers Orchestra")
    )
    song_1 = Song.objects.create(album=album, name="Kontroll på kontinentet")
    song_2 = Song.objects.create(album=album, name="Ompa til du dør")

    songs = list(
        Song.objects.dataclasses(
            dataclass=SongWithAlbumName, album_name=F("album__name"),
        ).order_by("name")
    )

    assert songs == [
        SongWithAlbumName(name=song_1.name, album_name=album.name),
        SongWithAlbumName(name=song_2.name, album_name=album.name),
    ]


def test_missing_fields_raises():
    """
    Test that an expection is raised if a field is missing.
    """

    # album_name is not specified and not a field on the class
    with pytest.raises(
        TypeError, match='Missing field "album_name" on dataclass "SongWithAlbumName"'
    ):
        Song.objects.dataclasses(dataclass=SongWithAlbumName)


def test_unknown_field_raises():
    """
    Test that an expection is raised if a field is missing.
    """

    # album_name is not specified and not a field on the class
    with pytest.raises(
        TypeError, match='Unknown field "some_field" on dataclass "SongWithAlbumName"'
    ):
        Song.objects.dataclasses(
            dataclass=SongWithAlbumName,
            album_name=F("album__name"),
            some_field=F("name"),
        )


@pytest.mark.usefixtures("db")
def test_override_django_field():
    """
    Test that overriding the value of a field name that matches a model field
    name is allowed.
    """

    album = Album.objects.create(
        name="Ompa til du dør", artist=Artist(name="Kaizers Orchestra")
    )
    Song.objects.create(album=album, name="Kontroll på kontinentet")

    song_dataclass = Song.objects.dataclasses(
        dataclass=SongWithAlbumName,
        name=Value("Some other name", output_field=TextField()),
        album_name=F("album__name"),
    ).get()

    assert song_dataclass == SongWithAlbumName(
        name="Some other name", album_name=album.name
    )


@pytest.mark.usefixtures("db")
def test_fields_with_defaults():
    """
    Test that overriding the value of a field name that matches a model field
    name is allowed.
    """

    album = Album.objects.create(
        name="Ompa til du dør", artist=Artist(name="Kaizers Orchestra")
    )
    song = Song.objects.create(album=album, name="Kontroll på kontinentet")

    song_dataclass = Song.objects.dataclasses(dataclass=SongWithLikes).get()
    assert song_dataclass == SongWithLikes(name=song.name)

    song_dataclass = Song.objects.dataclasses(
        dataclass=SongWithLikes, like_count=Value(2, output_field=IntegerField())
    ).get()
    assert song_dataclass == SongWithLikes(name=song.name, like_count=2)

    song_dataclass = Song.objects.dataclasses(
        dataclass=SongWithLikes,
        liked_by=Value(["a", "b"], output_field=ArrayField(TextField())),
    ).get()
    assert song_dataclass == SongWithLikes(name=song.name, liked_by=["a", "b"])
