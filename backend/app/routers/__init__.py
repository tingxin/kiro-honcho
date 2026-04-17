"""API routers."""
from .auth import router as auth_router
from .accounts import router as accounts_router
from .users import router as users_router
from .subscriptions import router as subscriptions_router
from .logs import router as logs_router
from .batch import router as batch_router
from .canceled_subscriptions import router as canceled_subscriptions_router
from .global_subscriptions import router as global_subscriptions_router

__all__ = [
    "auth_router",
    "accounts_router",
    "users_router",
    "subscriptions_router",
    "logs_router",
    "batch_router",
    "canceled_subscriptions_router",
    "global_subscriptions_router",
]
