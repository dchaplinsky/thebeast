"""
This module is shamelessly borrowed from django_jinja project and updated
with docstrings and type hints.

Copyright (c) 2012-2013 Andrey Antukh <niwi@niwi.be>, Phillip Marshall and other contributors
"""

from typing import Callable, Optional
import jinja2


# Global register dict for third party
# template functions, filters and extensions.
_local_env = {
    "globals": {},
    "tests": {},
    "filters": {},
    "extensions": set(),
}


def update_jinja_env(env: jinja2.Environment) -> None:
    """
    Update the given Jinja2 environment with third-party collected environment extensions.

    Args:
        env (jinja2.Environment): The Jinja2 environment to update.
    """
    env.globals.update(_local_env["globals"])
    env.tests.update(_local_env["tests"])
    env.filters.update(_local_env["filters"])

    for extension in _local_env["extensions"]:
        env.add_extension(extension)


def _attach_function(attr: str, func: Callable, name: Optional[str] = None) -> Callable:
    """
    Attach a function to the local environment.

    Args:
        attr (str): The attribute to attach the function to (e.g., 'globals', 'tests', 'filters').
        func (Callable): The function to attach.
        name (Optional[str]): The name to use for the function. If None, the function's __name__ is used.

    Returns:
        Callable: The attached function.
    """
    if name is None:
        name = func.__name__

    global _local_env
    _local_env[attr][name] = func
    return func


def _register_function(
    attr: str, name: Optional[str] = None, fn: Optional[Callable] = None
) -> Callable:
    """
    Register a function to the local environment.

    Args:
        attr (str): The attribute to register the function to (e.g., 'globals', 'tests', 'filters').
        name (Optional[str]): The name to use for the function. If None, the function's __name__ is used.
        fn (Optional[Callable]): The function to register. If None, a decorator is returned.

    Returns:
        Callable: The registered function or a decorator.
    """
    if name is None and fn is None:

        def dec(func: Callable) -> Callable:
            return _attach_function(attr, func)

        return dec

    elif name is not None and fn is None:
        if callable(name):
            return _attach_function(attr, name)
        else:

            def dec(func: Callable) -> Callable:
                return _register_function(attr, name, func)

            return dec

    else:
        return _attach_function(attr, fn, name)


def test(*args, **kwargs) -> Callable:
    """
    Register a test function to the local environment.

    Returns:
        Callable: The registered test function or a decorator.
    """
    return _register_function("tests", *args, **kwargs)


def filter(*args, **kwargs) -> Callable:
    """
    Register a filter function to the local environment.

    Returns:
        Callable: The registered filter function or a decorator.
    """
    return _register_function("filters", *args, **kwargs)
