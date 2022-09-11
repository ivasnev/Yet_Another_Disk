from datetime import date, datetime, timedelta

from asyncpg.pgproto.pgproto import UUID

from aiohttp.web_response import Response
from aiohttp_apispec import docs
from aiohttp.web import json_response
from aiohttp_pydantic import PydanticView

from YetAnotherDisk.api.schema import ErrorSchema, HistorySchema, IdSchema, DATE_FORMAT, DATE_FORMAT_m
from YetAnotherDisk.db.schema import updates_table, items_table
from sqlalchemy import and_
from .base import BaseView

import pytz
import json


class HistoryView(BaseView, PydanticView):
    URL_PATH = r'/node/{id}/history'

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat(timespec='milliseconds')[:-6] + "Z"
        if isinstance(obj, UUID):
            return str(obj)
        raise TypeError("Type %s not serializable" % type(obj))

    def get_valid_dates(self):
        date_s, date_e = None, None
        try:
            date_s = datetime.strptime(self.request.rel_url.query.get('dateStart'), DATE_FORMAT)
        except ValueError:
            pass
        try:
            date_e = datetime.strptime(self.request.rel_url.query.get('dateEnd'), DATE_FORMAT)
        except ValueError:
            pass
        try:
            date_s = datetime.strptime(self.request.rel_url.query.get('dateStart'), DATE_FORMAT_m)
        except ValueError:
            pass
        try:
            date_e = datetime.strptime(self.request.rel_url.query.get('dateEnd'), DATE_FORMAT_m)
        except ValueError:
            pass
        return date_s, date_e

    @docs(summary='Получить историю обновлений фала',
          parameters=[{
              'in': 'query',
              'name': 'date',
              'schema': HistorySchema,
              'required': 'true'
          }, {
              'in': 'path',
              'name': 'id',
              'schema': IdSchema,
              'required': 'true'
          }],
          responses={
              200: {"description": "Success operation"},
              400: {"schema": ErrorSchema,
                    "description": "Validation error"},
              404: {"schema": ErrorSchema,
                    "description": "Item not found"},
          })
    async def get(self, id: str, /):
        date_start, date_end = self.get_valid_dates()
        if date_start is None or date_end is None:
            errors = {'msg': "Validation error",
                      'code': 400}
            return json_response(status=400, data=errors)
        async with self.pg.transaction() as conn:
            unit = await conn.fetchrow(items_table.select().where(items_table.c.id == id))
            if not unit:
                return Response(status=404)
            query = updates_table.select().where(
                and_(updates_table.c.date >= date_start,
                     updates_table.c.date <= date_end,
                     updates_table.c.id == id))
            res = await conn.fetch(query)
            items = [dict(item) for item in res]
            data = json.dumps({'items': items}, default=self.json_serial)
        return Response(status=200, body=data)
