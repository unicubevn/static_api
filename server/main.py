from typing import Union

from dotenv import dotenv_values
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from hypercorn import logging
from hypercorn.config import Config
from server.doc_metadata import tags_metadata, servers_metadata
from router.api import router as api_router
from router.producer_rabbitmq import router as rabbitmq_router

_logger = logging.Logger(Config())

origins = [
    "http://localhost",
    "http://localhost:8080",
]

# Meta for docs
description = """
UniCube API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""
env = dotenv_values(".env")

app = FastAPI(
    debug=env["ENVIRONMENT"] == "dev",
    default_response_class=ORJSONResponse,
    title="UniCube Apis",
    description=description,
    openapi_url="/api/v1/openapi.json",
    openapi_tags=tags_metadata,
    servers=servers_metadata,
    summary="UniCube Apis for daily user",
    version="0.0.1",
    terms_of_service="https://unicube.vn/terms/",
    contact={
        "name": "UniCube JSC",
        "url": "https://unicube.vn/contact/",
        "email": "community@unicube.me",
    },
    license_info={
        "name": "Apache 2.0",
        "identifier": "MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include api path
# app.include_router(StudentRouter, tags=["Student"], prefix="/students")
app.include_router(api_router, tags=["API"], prefix="/api")
app.include_router(rabbitmq_router, tags=["RabbitMQ"], prefix="/rabbit")


@app.get("/")
async def read_root():
    await _logger.info("Hello this is UniCube Apis for daily use")
    return {"msg": "Hello this is UniCube Apis for daily use"}
