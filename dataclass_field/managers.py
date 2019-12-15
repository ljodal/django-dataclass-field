import dataclasses
from typing import Callable, Dict, Type, Union

from django.db.models import Expression, QuerySet
from django.db.models.query import BaseIterable


class DataclassesIterable(BaseIterable):
    """
    Iterable returned by QuerySet.dataclasses() that yields a dataclass
    instance for each row.
    """

    def __init__(
        self, *args, dataclass: Type, field_map: Dict[str, str], **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.dataclass = dataclass
        self.field_map = field_map

    def __iter__(self):
        queryset = self.queryset
        query = queryset.query
        compiler = query.get_compiler(queryset.db)

        # extra(select=...) cols are always at the start of the row.
        names = [
            *query.extra_select,
            *query.values_select,
            *query.annotation_select,
        ]

        for row in compiler.results_iter(
            chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size
        ):
            yield self.dataclass(
                **{self.field_map[name]: row[i] for i, name in enumerate(names)}
            )


def _dataclass_iterable(
    dataclass: Type, field_map: Dict[str, str]
) -> Callable[[], DataclassesIterable]:
    """
    Internal helper to provide extra context to the iterable when initialized
    by the queryset.
    """

    def func(*args, **kwargs) -> DataclassesIterable:
        return DataclassesIterable(
            *args, dataclass=dataclass, field_map=field_map, **kwargs
        )

    return func


class DataclassesQuerySet(QuerySet):
    """
    An extension to the Django QuerySet that adds a QuerySet.dataclasses()
    method that returns rows as instances of a given dataclass.
    """

    def dataclasses(
        self, *, dataclass: Type, **expressions: Expression
    ) -> "DataclassesQuerySet":
        """
        Returns a queryset that returns instances of the given dataclass.
        """

        # pylint: disable=protected-access

        # Make sure a dataclass was given
        assert dataclasses.is_dataclass(dataclass)

        # We need to make sure none of the expressions collide with any of the
        # model's field names, as Django does not allow this.
        model_field_names = {
            field.attname if hasattr(field, "attname") else field.name
            for field in self.model._meta.get_fields()
        }

        # Create a lookup table to find fields by name
        dataclass_fields = {
            field.name: field for field in dataclasses.fields(dataclass) if field.init
        }

        _expressions: Dict[str, Expression] = {}
        _field_map: Dict[str, str] = {}
        for field_name, expression in expressions.items():
            name = field_name

            # Make sure the specified name matches a field on the dataclass.
            if name not in dataclass_fields:
                raise TypeError(
                    f'Unknown field "{name}" on dataclass "{dataclass.__name__}"'
                )

            # Make sure the specified name does not collide with any of the
            # model's field names. Django does not allow this. We solve this by
            # appending an _ to the field name until it's unique.
            if name in model_field_names:
                while name in model_field_names or name in _expressions:
                    name = f"_{name}"

            _field_map[name] = field_name
            _expressions[name] = expression

        # Loop through the fields of the dataclass to make sure all fields
        # without a default is specified.
        for field_name, field in dataclass_fields.items():
            # Skip fields that are already specified
            if field_name in expressions:
                continue

            # If the field matches a field on the model, use that
            if field_name in model_field_names:
                _field_map[field_name] = field_name
                continue

            # Skip fields that have a default value
            if (
                field.default != dataclasses.MISSING
                or field.default_factory != dataclasses.MISSING
            ):
                continue

            raise TypeError(
                f'Missing field "{field_name}" on dataclass "{dataclass.__name__}"'
            )

        clone = self._values(*_field_map.keys(), **_expressions)
        clone._iterable_class = _dataclass_iterable(dataclass, _field_map)
        return clone
