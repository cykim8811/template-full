from app.core.arq import get_redis_settings


class WorkerSettings:
    functions = []
    redis_settings = get_redis_settings()
