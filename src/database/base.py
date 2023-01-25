from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, sql
from sqlalchemy.ext.declarative import as_declarative, declared_attr

from utils import camel_to_snake

# Base: TypeAlias = orm.declarative_base()  # type: ignore

# @as_declarative()
# class Base:
#     id: Any
#     __name__: str

#     # Generate __tablename__ automatically

#     @declared_attr  # type: ignore
#     def __tablename__(cls):  # noqa: N805
#         return cls.__name__.lower()


@as_declarative()
class BaseModel:
    __abstract__ = True
    __table_args__ = {'extend_existing': True}  # ???

    id: int = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=sql.func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=sql.func.now())

    @declared_attr
    def __tablename__(cls):
        return camel_to_snake(cls.__name__).replace('_model', '') + 's'

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id=})>'
