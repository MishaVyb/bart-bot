from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, sql
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Mapped

from utils import camel_to_snake


@as_declarative()
class BaseModel:
    __abstract__ = True
    __table_args__ = {'extend_existing': True}  # ???

    id: Mapped[int] = Column(
        BigInteger,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=sql.func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=sql.func.now())

    @declared_attr
    def __tablename__(cls):
        return camel_to_snake(cls.__name__).replace('_model', '') + 's'

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id=})>'
