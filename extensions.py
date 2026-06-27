"""
Shared Flask extensions — import this module to access the limiter
without circular-import issues.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,
    default_limits=["2000 per day", "200 per hour"],
    storage_uri="memory://"
)
