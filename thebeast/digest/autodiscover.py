from typing import List
from .utils import import_string
from .jinja_utils import update_jinja_env
from .resolvers import JINJA_ENV


def autodiscover(imports: List[str]):
    """
    Autodiscover the given modules and run their install functions.
    """

    for module in imports:
        # TODO: Do we really need to call it, if jinja stuff is registered automatically?
        module_setup = import_string(module + ".install")
        module_setup()

    update_jinja_env(JINJA_ENV)
