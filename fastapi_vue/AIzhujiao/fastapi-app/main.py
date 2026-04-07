from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from service import api
from dependences.db import engine
from dependences.migrate import run_migrations

router = api.router
app = FastAPI()

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 把 api.py 里的所有接口挂载进来
app.include_router(router)


@app.on_event("startup")
def _startup_migrate() -> None:
    run_migrations(engine)