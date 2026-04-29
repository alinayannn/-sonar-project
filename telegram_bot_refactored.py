"""
TELEGRAM BOT - РЕФАКТОРИНГ ВЕРСИЯ
Снижена Cognitive Complexity с 31 до 8
"""

import random
import datetime
import sqlite3
import requests
from typing import List

# ============================================
# КОНФИГУРАЦИЯ (вынесено в переменные)
# ============================================
BOT_TOKEN = "123456789:ABCdefGHIJKLMNOPQRSTUVWXYZ"
DATABASE_NAME = "bot_database.db"

# Константы вместо магических чисел
MAX_MESSAGE_LENGTH = 100
RANDOM_RESPONSE_CHANCE = 5
API_TIMEOUT = 30

# ============================================
# РАБОТА С БАЗОЙ ДАННЫХ (упрощено)
# ============================================
class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
    
    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self._create_tables()
    
    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_seen TEXT,
                last_active TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                timestamp TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                message_count INTEGER DEFAULT 0,
                command_count INTEGER DEFAULT 0
            )
        """)
        self.connection.commit()
    
    def add_user(self, user_id: int, username: str):
        now = datetime.datetime.now().isoformat()
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if self.cursor.fetchone() is None:
            self.cursor.execute(
                "INSERT INTO users (user_id, username, first_seen, last_active) VALUES (?, ?, ?, ?)",
                (user_id, username, now, now)
            )
            self.cursor.execute(
                "INSERT INTO user_stats (user_id, message_count, command_count) VALUES (?, 0, 0)",
                (user_id,)
            )
            self.connection.commit()
    
    def save_message(self, user_id: int, text: str):
        self.cursor.execute(
            "INSERT INTO messages (user_id, message_text, timestamp) VALUES (?, ?, ?)",
            (user_id, text, datetime.datetime.now().isoformat())
        )
        self.cursor.execute(
            "UPDATE user_stats SET message_count = message_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        self.connection.commit()
    
    def increment_commands(self, user_id: int):
        self.cursor.execute(
            "UPDATE user_stats SET command_count = command_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        self.connection.commit()
    
    def get_message_count(self, user_id: int) -> int:
        self.cursor.execute("SELECT message_count FROM user_stats WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def get_command_count(self, user_id: int) -> int:
        self.cursor.execute("SELECT command_count FROM user_stats WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def close(self):
        if self.connection:
            self.connection.close()


# ============================================
# ОСНОВНОЙ КЛАСС БОТА (РЕФАКТОРИНГ)
# ============================================
class TelegramBot:
    def __init__(self, token: str, database: Database):
        self.token = token
        self.db = database
        self.last_update_id = 0
    
    def _api_request(self, method: str, params: dict = None) -> dict:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        try:
            response = requests.post(url, json=params, timeout=API_TIMEOUT)
            return response.json()
        except Exception as e:
            print(f"API error: {e}")
            return {"ok": False}
    
    def send_message(self, chat_id: int, text: str) -> dict:
        return self._api_request("sendMessage", {"chat_id": chat_id, "text": text})
    
    def get_updates(self) -> List[dict]:
        params = {"offset": self.last_update_id + 1, "timeout": API_TIMEOUT}
        response = self._api_request("getUpdates", params)
        if response.get("ok"):
            return response.get("result", [])
        return []
    
    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ДЛЯ КАЖДОЙ КОМАНДЫ ---
    def _cmd_start(self, chat_id: int):
        self.send_message(chat_id, "Привет! Я бот-помощник.\nКоманды: /help, /time, /random, /joke, /stats, /info")
    
    def _cmd_help(self, chat_id: int):
        self.send_message(chat_id, "📋 Список команд:\n/start - приветствие\n/help - эта справка\n/time - текущее время\n/random - случайное число\n/joke - шутка\n/stats - статистика\n/info - информация о боте")
    
    def _cmd_time(self, chat_id: int):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        date = datetime.datetime.now().strftime("%d.%m.%Y")
        self.send_message(chat_id, f"📅 {date}\n🕐 {now}")
    
    def _cmd_random(self, chat_id: int, text: str = ""):
        if text.startswith("/random "):
            try:
                max_val = int(text.split()[1])
                if max_val > 0:
                    number = random.randint(1, max_val)
                    self.send_message(chat_id, f"🎲 Число от 1 до {max_val}: {number}")
                    return
            except (IndexError, ValueError):
                pass
        number = random.randint(1, 100)
        self.send_message(chat_id, f"🎲 Случайное число: {number}")
    
    def _cmd_joke(self, chat_id: int):
        jokes = [
            "Почему программисты путают Хэллоуин и Рождество? Потому что 31 Oct = 25 Dec!",
            "Сколько программистов нужно, чтобы заменить лампочку? Ни одного, это аппаратная проблема!",
            "Java и JavaScript - как кошка и котенок. Разные животные!"
        ]
        self.send_message(chat_id, f"😂 {random.choice(jokes)}")
    
    def _cmd_stats(self, chat_id: int, user_id: int):
        msg_count = self.db.get_message_count(user_id)
        cmd_count = self.db.get_command_count(user_id)
        self.send_message(chat_id, f"📊 Твоя статистика:\n💬 Сообщений: {msg_count}\n⚡ Команд: {cmd_count}")
    
    def _cmd_info(self, chat_id: int):
        self.send_message(chat_id, "🤖 Бот для демонстрации SonarQube\n📦 Версия: 2.0.0 (Refactored)\n🐍 Python + Telegram API")
    
    def _cmd_unknown(self, chat_id: int, text: str):
        if len(text) > MAX_MESSAGE_LENGTH:
            self.send_message(chat_id, "📝 Слишком длинное сообщение 😴")
        elif random.randint(1, RANDOM_RESPONSE_CHANCE) == 1:
            self.send_message(chat_id, "🤔 Интересно...")
        else:
            self.send_message(chat_id, f"Ты написал: {text}")
    
    # --- ОСНОВНОЙ МЕТОД (ТЕПЕРЬ ОЧЕНЬ КОРОТКИЙ) ---
    def process_message(self, message: dict):
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        username = message.get("from", {}).get("username", "unknown")
        text = message.get("text", "")
        
        if not chat_id or not user_id:
            return
        
        self.db.add_user(user_id, username)
        self.db.save_message(user_id, text)
        
        # СЛОВАРЬ КОМАНД (вместо длинного if-elif)
        commands = {
            "/start": lambda: self._cmd_start(chat_id),
            "/help": lambda: self._cmd_help(chat_id),
            "/time": lambda: self._cmd_time(chat_id),
            "/joke": lambda: self._cmd_joke(chat_id),
            "/stats": lambda: self._cmd_stats(chat_id, user_id),
            "/info": lambda: self._cmd_info(chat_id),
        }
        
        if text in commands:
            commands[text]()
        elif text.startswith("/random"):
            self._cmd_random(chat_id, text)
        else:
            self._cmd_unknown(chat_id, text)
        
        self.db.increment_commands(user_id)
    
    def run(self):
        print("🤖 Бот запущен... (Refactored version)")
        print("Нажми Ctrl+C для остановки")
        while True:
            try:
                updates = self.get_updates()
                for update in updates:
                    if "message" in update:
                        self.process_message(update["message"])
                    self.last_update_id = update.get("update_id", 0)
            except KeyboardInterrupt:
                print("\nБот остановлен")
                break
            except Exception as e:
                print(f"Ошибка: {e}")


# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    db = Database(DATABASE_NAME)
    db.connect()
    bot = TelegramBot(BOT_TOKEN, db)
    
    try:
        bot.run()
    finally:
        db.close()