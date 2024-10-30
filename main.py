from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response, Form
from fastapi.templating import Jinja2Templates
from typing import List
from time_command import TimeCommand  # Импортируем наш класс для парсинга времени

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class SocketManager:
    def __init__(self):
        self.active_connections: List[(WebSocket, str)] = []

    async def connect(self, websocket: WebSocket, user: str):
        await websocket.accept()
        self.active_connections.append((websocket, user))

    def disconnect(self, websocket: WebSocket, user: str):
        self.active_connections.remove((websocket, user))

    async def broadcast(self, data):
        for connection in self.active_connections:
            await connection[0].send_json(data)

manager = SocketManager()

# Инициализируем TimeCommand с путем к драйверу браузера
time_command = TimeCommand(driver_path="C:\\Users\\Sanek\\Desktop\\Chat_Fast_API")  # Замените на реальный путь

async def handle_command(message, sender):
    # Команда /help
    if message.startswith("/help"):
        return {"sender": "System", "message": "Доступные команды: /help, /time <город>"}

    elif message.startswith("/time"):
        # Обрабатываем команду /time
        time_message = time_command.execute(message, sender)
        return {"sender": "System", "message": time_message}

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
                    await manager.broadcast(data)
        except WebSocketDisconnect:
            manager.disconnect(websocket, sender)
            await manager.broadcast({"sender": sender, "message": "left the chat"})

@app.get("/")
def get_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/chat")
def get_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
