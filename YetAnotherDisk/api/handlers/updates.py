from datetime import date, datetime, timedelta

from asyncpg.pgproto.pgproto import UUID

from aiohttp.web_response import Response
from aiohttp_apispec import docs
from aiohttp.web import json_response

from YetAnotherDisk.api.schema import ErrorSchema, UpdatesSchema, DATE_FORMAT, DATE_FORMAT_m
from YetAnotherDisk.db.schema import items_table
from sqlalchemy import and_
from .base import BaseView

import pytz
import json


class UpdatesView(BaseView):
    URL_PATH = r'/updates'

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat(timespec='milliseconds')[:-6] + "Z"
        if isinstance(obj, UUID):
            return str(obj)
        raise TypeError("Type %s not serializable" % type(obj))


    def get_valid_date(self):
        _date = None
        try:
            _date = datetime.strptime(self.request.rel_url.query.get('date'), DATE_FORMAT)
        except ValueError:
            pass
        try:
            _date = datetime.strptime(self.request.rel_url.query.get('date'), DATE_FORMAT_m)
        except ValueError:
            pass
        return _date

    @docs(summary='Получить информацию об обновлениях файлов за 24 часа',
          parameters=[{
              'in': 'query',
              'name': 'date',
              'schema': UpdatesSchema,
              'required': 'true'
          }],
          responses={
              200: {"description": "Success operation"},
              400: {"schema": ErrorSchema,
                    "description": "Validation error"},
              404: {"schema": ErrorSchema,
                    "description": "Item not found"},
          })
    async def get(self):
        _date = self.get_valid_date()
        if _date is None:
            errors = {'msg': "Validation error",
                      'code': 400}
            return json_response(status=400, data=errors)
        async with self.pg.transaction() as conn:
            date_after = _date - timedelta(1)
            date_before = _date
            query = items_table.select().where(
                and_(items_table.c.date >= date_after,
                     items_table.c.date <= date_before,
                     items_table.c.type == 'FILE')
            )
            res = await conn.fetch(query)
            items = [dict(item) for item in res]
            data = json.dumps({'items': items}, default=self.json_serial)
        return Response(status=200, body=data)
