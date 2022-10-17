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
print(client)
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


# 신규 유저 추가(유저 테이블 업데이트) -> '내 페이지 만들기' 버튼을 통해 활성화(로그인 이후)
@app.post("/api/v1/rolling/user", response_description="Add new user", response_model=User)
async def create_user(user: User = Body(...)):
    user = jsonable_encoder(user)
    user_id = user["user_id"]

    user_exist = await db[USR_COLLECTION].find_one({"user_id": user_id})
    if user_exist is not None:
        _raiseException(409, f"User {user_id} already exists")

    new_user = await db[USR_COLLECTION].insert_one(user)
    created_user = await db[USR_COLLECTION].find_one({"_id": new_user.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


# 뒷 단 정도에서 필요할 법한
@app.get("/api/v1/rolling/users", response_description="List all users", response_model=List[User])
async def list_users():
    users = await db[USR_COLLECTION].find().to_list(1000)
    return JSONResponse(status_code=status.HTTP_200_OK, content=users)


# paper 테이블에 넣을 사용자 입력 메시지(페이지 주인(user_id), 지금 로그인한 사용자, 입력한 메시지 필요)
@app.put("/api/v1/rolling/message/{user_id}", response_description="Add a message", response_model=User)
async def update_message(user_id: str, message: Message = Body(...)):
    msg = {k: v for k, v in message.dict().items() if v is not None}

    if len(msg) >= 1:
        update_result = await db[USR_COLLECTION].update_one({"user_id": user_id}, {"$push": {"messages": msg}})
        # update_result.modified_count > 1 이면??
        if update_result.modified_count == 1:
            updated_user = await db[USR_COLLECTION].find_one({"user_id": user_id})
            if updated_user is not None:
                return JSONResponse(status_code=status.HTTP_201_CREATED, content=updated_user)

    # 위에서 업데이트를ㄹ 했는데 여기는 뭐하는??
    existing_user = await db[USR_COLLECTION].find_one({"user_id": user_id})
    if existing_user is not None:
        return existing_user

    _raiseException(404, f"User {user_id} not found")


# 해당 페이지에 걸려있는 메시지들 모두 return
@app.get("/api/v1/rolling/message/{user_id}", response_description="List all messages", response_model=List[Message])
async def list_messages(user_id: str):
    user = await db[USR_COLLECTION].find_one({"user_id": user_id})
    if user is None:
        _raiseException(404, f"User {user_id} not found")
    messages = user["messages"]
    return JSONResponse(status_code=status.HTTP_200_OK, content=messages)


def _raiseException(status_code, detail):
    raise HTTPException(status_code=status_code, detail=detail)
