"""
Модуль содержит схемы для валидации данных в запросах и ответах.

Схемы валидации запросов используются в бою для валидации данных отправленных
клиентами.

Схемы валидации ответов *ResponseSchema используются только при тестировании,
чтобы убедиться что обработчики возвращают данные в корректном формате.
"""
import time

from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import DateTime, Int, Nested, Str
from marshmallow.validate import Length, OneOf, Range
from YetAnotherDisk.db.schema import SystemItemType

DATE_FORMAT_m = '%Y-%m-%dT%H:%M:%S.%f%z'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'


class SystemItemImport(Schema):
    id = Str(required=True, allow_none=False)
    url = Str(validate=Length(min=1, max=255), required=False)
    parentId = Str(required=False, allow_none=True)
    type = Str(validate=OneOf([type.value for type in SystemItemType]), required=True)
    size = Int(validate=Range(min=0), required=False)

    @validates_schema
    def validate_size_and_url(self, item: dict, **_):
        if item.get('size'):
            if (item['type'] == 'FOLDER' and item['size'] is not None) or (
                    item['type'] == 'FILE' and item['size'] <= 0):
                raise ValidationError(
                    '%r size is not correct' % item['id']
                )
        if item.get('url'):
            if item['type'] == 'FOLDER' and item['url'] is not None:
                raise ValidationError(
                    'Folder url %r must be Null' % item['id']
                )


class SystemItemImportRequest(Schema):
    items = Nested(SystemItemImport, many=True, required=True,
                   validate=Length(max=10000))
    updateDate = DateTime(required=True, timezone=True)


    @validates_schema
    def validate_unique_id(self, data, **_):
        items_ids = set()
        for item in data['items']:
            if item['id'] in items_ids:
                raise ValidationError(
                    'item_id %r is not unique' % item['id']
                )
            items_ids.add(item['id'])


class UpdatesSchema(Schema):
    date = DateTime(required=True, timezone=True)

class HistorySchema(Schema):
    dateStart = DateTime(required=True, timezone=True)
    dateEnd = DateTime(required=True, timezone=True)

class IdSchema(Schema):
    id = Str(required=True)


class ErrorSchema(Schema):
    code = Int(required=True)
    message = Str(required=True)

