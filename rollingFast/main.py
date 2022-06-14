from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/v1/rolling/topic")
def create_topic(user_id: str, topic_name: str):
    #TODO: create topic -> topic link 생성, topic_name, user_id 를 db에 저
    return {"topic_link": topic_name+"_link", "topic_name": topic_name, "user_id": user_id}


@app.post("/api/v1/rolling/message")
def create_topic(user_id: str, topic_link: str, message: str):
    return {"topic_link": topic_link, "user_id": user_id, "message": message}장


@app.get("/api/v1/rolling/topic")
def show_topic(user_id: str, topic_link: str):
    #TODO: return 해당 페이지 with message render
    return None

