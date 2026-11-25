from fastapi import FastAPI

from ..core.config import Settings
from . import admin, auth, backup, days, frontend, messages, milestones, plan, reviews, stats, timer


def register_routers(app: FastAPI, settings: Settings) -> None:
    for module in (auth, days, reviews, milestones, plan, timer, stats, backup, messages, admin):
        app.include_router(module.router)
    frontend.mount_frontend(app, settings.frontend_dist())
