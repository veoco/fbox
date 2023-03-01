import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from fbox import settings
from fbox.log import logger
from fbox.database import db
from fbox.preload import router as preload_router
from fbox.files.views import router as files_router
from fbox.cards.views import router as cards_router
from fbox.admin.views import router as admin_router


async def clean_data():
    while True:
        logger.info("Running clean data")

        await db.clean_expired_boxes()
        db.clean_expire_ip_user()

        logger.info("Clean data finished")
        await asyncio.sleep(settings.BOX_CLEAN_PERIOD)


async def startup():
    logger.info("Running startup task")

    await db.init()
    logger.info("Init database complete")

    asyncio.create_task(clean_data())

    logger.info("Startup task finished")


async def shutdown():
    await db.close()


app = FastAPI(
    debug=settings.DEBUG,
    title=settings.SITE_TITLE,
    docs_url="/api/docs" if settings.SITE_API_DOCS else None,
    openapi_url="/api/openapi.json" if settings.SITE_API_DOCS else None,
    on_startup=[startup],
    on_shutdown=[shutdown],
)

app.include_router(preload_router, prefix="")
app.include_router(files_router, prefix="/api")
app.include_router(cards_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.mount("", StaticFiles(directory=settings.WWW_ROOT), name="static")
