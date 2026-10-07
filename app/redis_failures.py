"""Redis failures the gateway treats as an unavailable store.

Connection and timeout errors from the stdlib are included because test
doubles and redis-py both raise them. Response errors from redis-py are
included so a broken command is not reported as an unhandled server error.
"""

from redis.exceptions import RedisError

REDIS_FAILURES: tuple[type[BaseException], ...] = (RedisError, OSError)
