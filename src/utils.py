import functools
import inspect
import re
from typing import Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from configurations import logger

_ModelType = TypeVar('_ModelType')


async def get_or_create(
    session: AsyncSession,
    model: Type[_ModelType],
    extra_kwargs: dict = {},
    **instance_kwargs,
) -> _ModelType:
    """
    Get or create model instance if it does not exist.

    `instance_kwargs`: taking for quering DB
    `extra_kwargs`: taking for instance creation united with `instance_kwargs`
    """

    result = await session.execute(select(model).filter_by(**instance_kwargs))
    if instance := result.scalar():
        return instance

    instance_kwargs |= extra_kwargs
    instance = model(**instance_kwargs)
    session.add(instance)

    logger.info(f'{instance} added to database. ')
    return instance


def camel_to_snake(case: str):
    case = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', case)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', case).lower()


def logcontext(wrapped):
    # FIXME
    # does not work for async function

    functools.wraps(wrapped)

    async def wrapper(*args, **kwargs):
        logger.debug(f'--> {wrapped.__name__} in -->')
        result = await wrapped(*args, **kwargs)
        logger.debug(f'<-- {wrapped.__name__} out <--')
        return result

    return wrapper


def get_func_name(previous: bool = False) -> str:
    frame = inspect.currentframe()

    # single back
    if not previous:
        if not frame or not frame.f_back:
            return '<no_func_name>'
        return frame.f_back.f_code.co_name

    # double back
    if not frame or not frame.f_back or not frame.f_back.f_back:
        return '<no_func_name>'
    return frame.f_back.f_back.f_code.co_name
