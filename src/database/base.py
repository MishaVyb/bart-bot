from datetime import datetime
from enum import Enum
from typing import Literal

from sqlalchemy import BIGINT, JSON, VARCHAR, BigInteger, Column, DateTime, sql
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column
from accessories import MediaType

from utils import camel_to_snake


class BaseModel(MappedAsDataclass, DeclarativeBase, kw_only=True):
    type_annotation_map = {
        int: BIGINT,
        dict: JSON,
        Literal: VARCHAR(256),
        Enum: VARCHAR(256),
        MediaType: VARCHAR(256),
    }

    id: Mapped[int] = mapped_column(primary_key=True, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=sql.func.now(), init=False, repr=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=sql.func.now(), onupdate=sql.func.now(), init=False, repr=False
    )

    @declared_attr
    def __tablename__(cls):
        return camel_to_snake(cls.__name__).replace('_model', '')
