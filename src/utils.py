import functools
import inspect
import re

from configurations import logger


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
