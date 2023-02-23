from datetime import datetime

from sqlalchemy import BIGINT, JSON, BigInteger, Column, DateTime, sql
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Mapped, DeclarativeBase, MappedAsDataclass, mapped_column

from utils import camel_to_snake


class BaseModel(MappedAsDataclass, DeclarativeBase, kw_only=True):
    type_annotation_map = {int: BIGINT, dict: JSON}
    # __abstract__ = True
    # __table_args__ = {'extend_existing': True}  # ???

    id: Mapped[int] = mapped_column(
        # nullable=False,
        # unique=True,
        primary_key=True,
        # autoincrement=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=sql.func.now(), init=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=sql.func.now(), onupdate=sql.func.now(), init=False)

    @declared_attr
    def __tablename__(cls):
        return camel_to_snake(cls.__name__).replace('_model', '')
