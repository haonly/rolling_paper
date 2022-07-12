from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List, Optional, Dict
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import motor.motor_asyncio

DB = 'rolling'
USR_COLLECTION = 'users'

username = 'admin'
password = 'mongo'

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://%s:%s@localhost:27017/' % (username, password))
db = client[DB]


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# User class defined in Pydantic
class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    name: str = Field(...)
    user_id: str = Field(...)
    messages: Optional[list] = []

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Ron",
                "user_id": "ron737",
                "messages": []
            }
        }


# Message class defined in Pydantic
class Message(BaseModel):
    from_id: str = Field(...)
    messages: str = Field(...)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/users", response_description="Add new user", response_model=User)
async def create_user(user: User = Body(...)):
    user = jsonable_encoder(user)
    user_id = user["user_id"]

    user_exist = await db[USR_COLLECTION].find_one({"user_id": user_id})
    if user_exist is not None:
        raise HTTPException(status_code=409, detail=f"User {user_id} already exists")

    new_user = await db[USR_COLLECTION].insert_one(user)
    created_user = await db[USR_COLLECTION].find_one({"_id": new_user.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@app.get("/users", response_description="List all users", response_model=List[User])
async def list_users():
    users = await db[USR_COLLECTION].find().to_list(1000)
    return users


@app.put("/{user_id}", response_description="Add a message", response_model=User)
async def update_message(user_id: str, message: Message = Body(...)):
    msg = {k: v for k, v in message.dict().items() if v is not None}

    if len(msg) >= 1:
        update_result = await db[USR_COLLECTION].update_one({"user_id": user_id}, {"$push": {"messages": msg}})

        if update_result.modified_count == 1:
            updated_user = await db[USR_COLLECTION].find_one({"user_id": user_id})
            if updated_user is not None:
                return updated_user

    existing_user = await db[USR_COLLECTION].find_one({"user_id": user_id})
    if existing_user is not None:
        return existing_user

    raise HTTPException(status_code=404, detail=f"User {user_id} not found")


@app.get("/{user_id}", response_description="List all messages", response_model=List[Message])
async def list_messages(user_id: str):
    user = await db[USR_COLLECTION].find_one({"user_id": user_id})
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    messages = user["messages"]
    return messages
