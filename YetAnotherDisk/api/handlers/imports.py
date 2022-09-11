from typing import Generator

from aiohttp.web_response import Response
from aiohttp_apispec import docs, request_schema
from aiomisc import chunk_list

from YetAnotherDisk.api.schema import SystemItemImportRequest, ErrorSchema
from YetAnotherDisk.db.schema import items_table, relations_table, updates_table
from YetAnotherDisk.utils.pg import MAX_QUERY_ARGS
from sqlalchemy import and_

from .base import BaseView


class ImportsView(BaseView):
    URL_PATH = '/imports'
    MAX_itemS_PER_INSERT = MAX_QUERY_ARGS // len(items_table.columns)
    MAX_RELATIONS_PER_INSERT = MAX_QUERY_ARGS // len(relations_table.columns)

    @classmethod
    def make_items_table_rows(cls, items, date) -> Generator:
        """
        Генерирует данные готовые для вставки в таблицу items.
        """
        for item in items:
            req = {'id': item['id'],
                   'type': item['type'],
                   'date': date,
                   }
            if 'url' in item:
                req['url'] = item['url']
            else:
                req['url'] = None
            if 'parentId' in item:
                req['parentId'] = item['parentId']
            else:
                req['parentId'] = None
            if 'size' in item:
                req['size'] = item['size']
            else:
                req['size'] = None
            yield req

    @classmethod
    def make_relations_table_rows(cls, items) -> Generator:
        """
        Генерирует данные готовые для вставки в таблицу relations.
        """
        for item in items:
            if item['parentId']:
                yield {
                    'unit_id': item['parentId'],
                    'relative_id': item['id'],
                }

    def make_updates_table_rows(cls, items, date) -> Generator:
        """
        Генерирует данные готовые для вставки в таблицу updates.
        """
        for item in items:
            yield {
                'id': item['id'],
                'date': date,
            }

    @classmethod
    async def update_item(cls, conn, _id, data):
        item_rel_id = await conn.fetchrow(items_table.select().where(items_table.c.id == _id))
        if item_rel_id:
            item_rel_id = item_rel_id['parentId']
            if item_rel_id != data['parentId']:
                query = relations_table.delete().where(
                    and_(relations_table.c.unit_id == item_rel_id,
                         relations_table.c.relative_id == _id))
                await conn.execute(query)
                query = relations_table.insert().values({
                    'unit_id': data['parentId'],
                    'relative_id': data['id'],
                })
                await conn.execute(query)
        query = items_table.update().values(data).where(
            items_table.c.id == _id
        )
        await conn.execute(query)
        
    async def update_size_for_folder(self, unit_id, conn):
        unit = await conn.fetchrow(items_table.select().where(items_table.c.id == unit_id))
        if unit['type'] == 'FILE':
            return unit['size']
        children = await conn.fetch(relations_table.select().where(relations_table.c.unit_id == unit_id))
        unit = dict(unit)
        total_size = 0
        for child in children:
            size = await self.update_size_for_folder(child['relative_id'], conn)
            total_size += size
        unit['size'] = total_size
        query = items_table.update().values(unit).where(
            items_table.c.id == unit_id
        )
        await conn.execute(query)

        return total_size

    @staticmethod
    async def get_roots_folders(conn, set_of_categories: set, date):
        result = set()
        seen_categories = set()
        for _cat in set_of_categories:
            seen_categories.add(_cat)
            _cur = _cat
            _next = await conn.fetchrow(relations_table.select().where(relations_table.c.relative_id == _cur))
            if not _next:
                result.add(_cur)
            while _next:
                _next = _next['unit_id']
                if _next in seen_categories:
                    break
                seen_categories.add(_next)
                _cur = _next
                _next = await conn.fetchrow(relations_table.select().where(relations_table.c.relative_id == _cur))
            else:
                result.add(_cur)
        for category_id in seen_categories:
            unit = await conn.fetchrow(items_table.select().where(items_table.c.id == category_id))
            if not unit:
                continue
            unit = dict(unit)
            unit['date'] = date
            query = items_table.update().values(unit).where(
                items_table.c.id == category_id
            )
            await conn.execute(query)
        return result


    @classmethod
    async def validate_parents(cls, conn, items):
        for item in items:
            if item['parentId'] is None:
                continue
            parent = await conn.fetchrow(items_table.select().where(items_table.c.id == item['parentId']))
            if parent['type'] == 'FILE':
                return False
        return True

    @docs(summary='Импорт файлов и папок, а также обновление их при повторном импорте',
          responses={
              200: {"description": "Success operation"},
              400: {"schema": ErrorSchema,
                    "description": "Validation error"},
          }, )
    @request_schema(SystemItemImportRequest())
    async def post(self):
        async with self.pg.transaction() as conn:
            items = self.request['data']['items']
            date = self.request['data']['updateDate']
            if not self.validate_parents(conn, items):
                return Response(status=400)
            items_to_ins = []

            folders_to_update = set()
            for item in items:
                if await conn.fetchrow(items_table.select().where(items_table.c.id == item['id'])):
                    parent_before = await conn.fetchrow(
                        relations_table.select().where(relations_table.c.relative_id == item['id']))
                    await self.update_item(conn, item['id'], item)
                    parent_after = await conn.fetchrow(
                        relations_table.select().where(relations_table.c.relative_id == item['id']))
                    if parent_before and parent_after and parent_before['unit_id'] == parent_after['unit_id']:
                        folders_to_update.add(parent_before['unit_id'])
                    else:
                        if parent_after:
                            folders_to_update.add(parent_after['unit_id'])
                        if parent_before:
                            folders_to_update.add(parent_before['unit_id'])
                else:
                    items_to_ins.append(item)
                    if item['parentId']:
                        folders_to_update.add(item['parentId'])
            
            item_rows = self.make_items_table_rows(items_to_ins, date)
            relation_rows = self.make_relations_table_rows(items_to_ins)
            updates_rows = self.make_updates_table_rows(items,date)
            chunked_item_rows = chunk_list(item_rows,
                                              self.MAX_itemS_PER_INSERT)
            chunked_relation_rows = chunk_list(relation_rows,
                                               self.MAX_RELATIONS_PER_INSERT)
            chunked_updates_rows = chunk_list(updates_rows,
                                               self.MAX_RELATIONS_PER_INSERT)
            query = items_table.insert()
            for chunk in chunked_item_rows:
                await conn.execute(query.values(list(chunk)))

            query = relations_table.insert()
            for chunk in chunked_relation_rows:
                await conn.execute(query.values(list(chunk)))

            if len(folders_to_update) != 0:
                folders_to_update = await self.get_roots_folders(conn, folders_to_update, date)
                for cat_id in folders_to_update:
                    await self.update_size_for_folder(cat_id, conn)

            query = updates_table.insert()
            for chunk in chunked_updates_rows:
                await conn.execute(query.values(list(chunk)))

        return Response(status=200)
