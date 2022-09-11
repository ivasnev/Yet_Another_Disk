from aiohttp.web_response import Response
from aiohttp_apispec import docs
from aiohttp_pydantic import PydanticView
from aiohttp.web import json_response


from YetAnotherDisk.api.schema import ErrorSchema, IdSchema
from YetAnotherDisk.db.schema import items_table, relations_table, updates_table
from sqlalchemy import and_

from .base import BaseView


class DeleteView(BaseView, PydanticView):
    URL_PATH = r'/delete/{id}'

    async def on_validation_error(self, exception, context):
        errors = {'msg': exception.errors()[0]['msg'],
                  'code': 400}

        return json_response(data=errors, status=400)

    @docs(summary='Удаление папки или файла',
          parameters=[{
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
    async def delete(self, id: str, /):
        async with self.pg.transaction() as conn:
            unit = await conn.fetchrow(items_table.select().where(items_table.c.id == id))
            if not unit:
                return Response(status=404)
            stack = [id]
            while len(stack) != 0:
                _id = stack.pop()
                # Удаляем текущий объект из таблицы элементов
                query = items_table.delete().where(
                    items_table.c.id == _id)
                await conn.execute(query)
                # Удаляем все обновления текущего объекта
                query = updates_table.delete().where(
                    updates_table.c.id == _id)
                await conn.execute(query)
                # Находим родственные связи и удаляем их
                query = relations_table.select().where(
                    relations_table.c.unit_id == _id)
                res = await conn.fetch(query)
                for row in res:
                    stack.append(row['relative_id'])
                    #Удаляем все связи родителей с текущим объектом
                    query = relations_table.delete().where(
                        and_(relations_table.c.unit_id == _id,
                             relations_table.c.relative_id == row['relative_id']))
                    await conn.execute(query)
                    # Удаляем все связи детей с текущим объектом
                    query = relations_table.delete().where(
                        relations_table.c.relative_id == _id)
                    await conn.execute(query)
        return Response(status=200)
