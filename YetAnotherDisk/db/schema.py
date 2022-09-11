from sqlalchemy import (
    Column, BigInteger,
    MetaData, String, Table,
    Enum as PgEnum, DateTime,
)
from enum import Enum, unique


@unique
class SystemItemType(Enum):
    file = 'FILE'
    folder = 'FOLDER'


convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)

items_table = Table(
    'items',
    metadata,
    Column('id', String, primary_key=True, nullable=False),
    Column('url', String, nullable=True),
    Column('date', DateTime(timezone=True), nullable=False),
    Column('parentId', String, nullable=True),
    Column('type', PgEnum(SystemItemType, name='type'), nullable=False),
    Column('size', BigInteger, nullable=True),
)

relations_table = Table(
    'relations',
    metadata,
    Column('unit_id', String, primary_key=True),
    Column('relative_id', String, primary_key=True),
)

updates_table = Table(
    'updates',
    metadata,
    Column('id', String, nullable=False,),
    Column('date', DateTime(timezone=True), nullable=False),
)
