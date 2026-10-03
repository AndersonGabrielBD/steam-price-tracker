"""Shared slowapi rate limiter. Lives in its own module (rather than
main.py) so routers/games.py can import it to decorate routes without a
circular import against main.py, which also needs it to wire up the app.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
