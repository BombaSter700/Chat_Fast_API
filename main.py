from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response, Form
from fastapi.templating import Jinja2Templates
from typing import List
from time_command import TimeCommand # Класс для парсинга времени

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class SocketManager:
    def __init__(self):
        self.active_connections: List[(WebSocket, str)] = []

    async def connect(self, websocket: WebSocket, user: str):
        await websocket.accept()
        self.active_connections.append((websocket, user))

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            (ws, u) for ws, u in self.active_connections if ws != websocket
        ]

    async def broadcast(self, data):
        for connection, _ in self.active_connections:
            await connection.send_json(data)

manager = SocketManager()

# Инициализируем TimeCommand с путем к драйверу браузера
_command = TimeCommand(driver_path="C:\\Users\\Sanek\\Desktop\\Chat_Fast_API") #поменять для своего пути

async def handle_command(message, sender):
    # Обрабатываем команды
    if message.startswith("/help"):
        return {"sender": "System", "message": "Доступные команды: /help, /time <город>, /weather <город>"}

    elif message.startswith("/time"):
        time_message = _command.execute_time(message, sender)
        return {"sender": "System", "message": time_message}
    
    elif message.startswith("/weather"):
        weather_message = _command.execute_weather(message, sender)
        return {"sender": "System", "message": weather_message}
    
    else:
        return {"sender": "System", "message": "Неизвестная команда. Введите /help для списка команд"}

@app.post("/api/register")
async def register_user(response: Response, nickname: str = Form(...)):
    response.set_cookie(key="X-Authorization", value=nickname, httponly=True)
    return {"message": "User registered"}

@app.get("/api/current_user")
def get_user(request: Request):
    return request.cookies.get("X-Authorization")

# обработка сообщений
@app.websocket("/api/chat")
async def chat(websocket: WebSocket):
    sender = websocket.cookies.get("X-Authorization")
    if sender:
        await manager.connect(websocket, sender)
        await manager.broadcast({"sender": sender, "message": "joined the chat"})
        try:
            while True:
                data = await websocket.receive_json()
                message = data.get("message")
                if message.startswith("/"):
                    command_response = await handle_command(message, sender)
                    await websocket.send_json(command_response)
                else:
                    await manager.broadcast({"sender": sender, "message": message})
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            await manager.broadcast({"sender": sender, "message": "left the chat"})

@app.get("/")
def get_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/chat")
def get_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
