from django.db import models

from dataclass_field import DataclassField
from dataclass_field.managers import DataclassesQuerySet

from .types import Artist


class Album(models.Model):
    """
    An album with a nested artist.
    """

    artist = DataclassField(dataclass=Artist)
    name = models.CharField(max_length=255)

    objects = DataclassesQuerySet.as_manager()


class Song(models.Model):
    """
    A song that belongs to an album.
    """

    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    objects = DataclassesQuerySet.as_manager()
