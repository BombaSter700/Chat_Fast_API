from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, Request, Response)
from typing import List
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class SocketManager:
    def __init__(self):
        self.active_connections: List[(WebSocket, str)] = []

    async def connect(self, websocket:WebSocket, user:str):
        await websocket.accept()
        self.active_connections.append((websocket, user))

    def disconnect(self, websocket:WebSocket, user:str):
        self.active_connections.remove((websocket, user))

    async def broadcast(self,data):
        for connection in self.active_connections:
            await connection[0].send_json(data)


manager = SocketManager()

@app.websocket("/api/chat")
async def chat(websocket: WebSocket):
    sender = websocket.cookies.get("X-Authorization")
    if sender:
        await manager.connect(websocket, sender)
        response = {
            "sender": sender,
            "message": "joined the chat"
        }
        await manager.broadcast(response)
        try:
            while True:
                data = await websocket.receive_json()
                await manager.broadcast(data)
        except WebSocketDisconnect:
            manager.disconnect(websocket, sender)
            response = {
                "sender": sender,
                "message": "left the chat"
            }
            await manager.broadcast(response)


@app.get("/api/current_user")
def get_user(request:Request):
    return request.cookies.get("X-Authorization")

nickname = 0
@app.post("/api/register")
def register_user(response: Response, request: Request):
    nickname = request.query_params.get("nickname")
    response.set_cookie(key="X-Authorization", value=nickname, httponly=True)
    return {"message": "User registered"}