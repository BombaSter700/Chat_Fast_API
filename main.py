import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from time_command import TimeCommand
from weather_command import WeatherCommand

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Путь к файлу с данными пользователей
USER_DATA_FILE = "C:\\Users\\Sanek\\Desktop\\Chat_Fast_API\\user_data.json"

class SocketManager:
    def __init__(self):
        self.active_connections: List[(WebSocket, str)] = []
        self.user_data = self.load_user_data()  # Загружаем данные из JSON при инициализации

    async def connect(self, websocket: WebSocket, user: str):
        await websocket.accept()
        self.active_connections.append((websocket, user))
        
        # Сохраняем данные пользователя при первом входе
        if user not in self.user_data:
            self.user_data[user] = {
                "first_appearance": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message_count": 0
            }
            self.save_user_data()  # Сохраняем данные в файл

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            (ws, u) for ws, u in self.active_connections if ws != websocket
        ]

    async def broadcast(self, data):
        for connection, _ in self.active_connections:
            await connection.send_json(data)

    def increment_message_count(self, user: str):
        if user in self.user_data:
            self.user_data[user]["message_count"] += 1
            self.save_user_data()  # Сохраняем данные в файл

    def get_user_info(self, user: str):
        if user in self.user_data:
            return self.user_data[user]
        return None

    def load_user_data(self):
        """Загружаем данные пользователей из JSON-файла."""
        try:
            with open(USER_DATA_FILE, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_user_data(self):
        """Сохраняем данные пользователей в JSON-файл."""
        with open(USER_DATA_FILE, "w") as file:
            json.dump(self.user_data, file, indent=4)

manager = SocketManager()

# Инициализируем TimeCommand и WeatherCommand с путем к драйверу браузера
time_command = TimeCommand(driver_path="C:\\Users\\Sanek\\Desktop\\Chat_Fast_API")
weather_command = WeatherCommand(driver_path="C:\\Users\\Sanek\\Desktop\\Chat_Fast_API")

async def handle_command(message, sender):
    # Обрабатываем команды
    if message == "/help":
        return {"sender": "System", "message": "Доступные команды: /help, /time <город>, /weather <город>, /userinfo"}

    elif message.startswith("/time"):
        time_message = time_command.execute_time(message, sender)
        return {"sender": "System", "message": time_message}
    
    elif message.startswith("/weather"):
        weather_message = weather_command.execute_weather(message, sender)
        return {"sender": "System", "message": weather_message}
    
    elif message == "/userinfo":
        user_info = manager.get_user_info(sender)
        if user_info:
            return {
                "sender": "System",
                "message": f"Информация о пользователе {sender}: Сообщений - {user_info['message_count']}, Первое появление - {user_info['first_appearance']}"
            }
        else:
            return {"sender": "System", "message": "Информация о пользователе не найдена."}
    
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
                    manager.increment_message_count(sender)
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
