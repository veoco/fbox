import asyncio
from fastapi import FastAPI

from fbox import settings
from fbox.log import logger
from fbox.database import db
from fbox.files.views import router as files_router
from fbox.cards.views import router as cards_router
from fbox.admin.views import router as admin_router


async def clean_data():
    while True:
        logger.info("Runing clean data")

        await db.clean_expired_boxes()
        db.clean_expire_ip_user()

        logger.info("Clean data finished")
        await asyncio.sleep(60)


async def startup():
    logger.info("Running startup task")

    asyncio.create_task(clean_data())

    logger.info("Startup task finished")


app = FastAPI(
    debug=settings.DEBUG,
    title="DBOX",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    on_startup=[startup],
)

app.include_router(files_router, prefix="/api")
app.include_router(cards_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
