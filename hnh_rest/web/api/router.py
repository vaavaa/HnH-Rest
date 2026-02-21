from fastapi.routing import APIRouter
from hnh_rest.web.api import echo
from hnh_rest.web.api import redis
from hnh_rest.web.api import docs
from hnh_rest.web.api import monitoring
from hnh_rest.web.api import prompts

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(docs.router)
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])
api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
api_router.include_router(prompts.router)
api_router.include_router(prompts.router_audit)
