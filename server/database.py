
import motor.motor_asyncio
from dotenv import dotenv_values
from pydantic import BeforeValidator
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

config = dotenv_values(".env")
client = motor.motor_asyncio.AsyncIOMotorClient(config["DB_URL"])
db = client.get_database(config["MONGO_DB"])
key_collection = db.get_collection(config["KEY_COLLECTION"])

