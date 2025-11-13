import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis_client() -> redis.Redis:
    return redis_client


def test_redis_connection() -> bool:
    try:
        redis_client.ping()
        return True
    except Exception as e:
        raise Exception(f"Redis connection failed: {str(e)}")
