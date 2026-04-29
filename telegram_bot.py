"""
TELEGRAM BOT - БОЛЬШОЙ КОД ДЛЯ SONARQUBE АНАЛИЗА
В этом коде есть:
- дублирование кода
- длинные методы
- магические числа
- проблемы с безопасностью
- высокая цикломатическая сложность
"""

import random
import datetime
import sqlite3
import requests
from typing import Dict, List, Optional, Tuple

# ============================================
# КОНФИГУРАЦИЯ (hardcoded token - это плохо для безопасности)
# ============================================
BOT_TOKEN = "123456789:ABCdefGHIJKLMNOPQRSTUVWXYZ"  # НЕ НАСТОЯЩИЙ ТОКЕН
DATABASE_NAME = "bot_database.db"

# ============================================
# РАБОТА С БАЗОЙ ДАННЫХ (тут есть дублирование кода)
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
    
    # ДУБЛИРОВАНИЕ: метод add_user почти такой же как update_user
    def add_user(self, user_id: int, username: str):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if self.cursor.fetchone() is None:
            now = datetime.datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO users (user_id, username, first_seen, last_active) VALUES (?, ?, ?, ?)",
                (user_id, username, now, now)
            )
            self.cursor.execute(
                "INSERT INTO user_stats (user_id, message_count, command_count) VALUES (?, 0, 0)",
                (user_id,)
            )
            self.connection.commit()
            return True
        return False
    
    # ДУБЛИРОВАНИЕ: этот метод почти как add_user
    def update_user(self, user_id: int, username: str):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if self.cursor.fetchone() is None:
            now = datetime.datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO users (user_id, username, first_seen, last_active) VALUES (?, ?, ?, ?)",
                (user_id, username, now, now)
            )
            self.cursor.execute(
                "INSERT INTO user_stats (user_id, message_count, command_count) VALUES (?, 0, 0)",
                (user_id,)
            )
        else:
            self.cursor.execute(
                "UPDATE users SET username = ?, last_active = ? WHERE user_id = ?",
                (username, datetime.datetime.now().isoformat(), user_id)
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
# ОСНОВНОЙ КЛАСС БОТА (тут очень длинный метод)
# ============================================
class TelegramBot:
    def __init__(self, token: str, database: Database):
        self.token = token
        self.db = database
        self.last_update_id = 0
    
    def _api_request(self, method: str, params: dict = None) -> dict:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        try:
            response = requests.post(url, json=params, timeout=30)
            return response.json()
        except Exception as e:
            print(f"API error: {e}")
            return {"ok": False}
    
    def send_message(self, chat_id: int, text: str) -> dict:
        return self._api_request("sendMessage", {"chat_id": chat_id, "text": text})
    
    def get_updates(self) -> List[dict]:
        params = {"offset": self.last_update_id + 1, "timeout": 30}
        response = self._api_request("getUpdates", params)
        if response.get("ok"):
            return response.get("result", [])
        return []
    
    # ЭТОТ МЕТОД СЛИШКОМ ДЛИННЫЙ (70+ строк) - это CODE SMELL
    # У него высокая цикломатическая сложность (много if/elif)
    def process_message(self, message: dict):
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        username = message.get("from", {}).get("username", "unknown")
        text = message.get("text", "")
        
        if not chat_id or not user_id:
            return
        
        self.db.add_user(user_id, username)
        self.db.save_message(user_id, text)
        
        # МНОГО if-elif (цикломатическая сложность > 10)
        if text == "/start":
            self.send_message(chat_id, "Привет! Я бот-помощник.\nКоманды: /help, /time, /random, /joke, /calc, /stats, /info, /echo")
        
        elif text == "/help":
            self.send_message(chat_id, "📋 Список команд:\n/start - приветствие\n/help - эта справка\n/time - текущее время\n/random - случайное число\n/joke - шутка\n/calc 2+2 - калькулятор\n/stats - твоя статистика\n/info - информация о боте\n/echo текст - повторить")
        
        elif text == "/time":
            now = datetime.datetime.now().strftime("%H:%M:%S")
            date = datetime.datetime.now().strftime("%d.%m.%Y")
            self.send_message(chat_id, f"📅 {date}\n🕐 {now}")
        
        elif text == "/random":
            number = random.randint(1, 100)
            self.send_message(chat_id, f"🎲 Случайное число: {number}")
        
        elif text.startswith("/random "):
            try:
                max_val = int(text.split()[1])
                if max_val <= 0:
                    self.send_message(chat_id, "Число должно быть больше 0")
                else:
                    number = random.randint(1, max_val)
                    self.send_message(chat_id, f"🎲 Число от 1 до {max_val}: {number}")
            except (IndexError, ValueError):
                self.send_message(chat_id, "Использование: /random [максимальное число]")
        
        elif text == "/joke":
            jokes = [
                "Почему программисты путают Хэллоуин и Рождество? Потому что 31 Oct = 25 Dec!",
                "Сколько программистов нужно, чтобы заменить лампочку? Ни одного, это аппаратная проблема!",
                "Java и JavaScript - как кошка и котенок. Разные животные!",
                "Программист просыпается ночью и шепчет: 'Где же моя точка с запятой?'",
                "Алкоголь: решение и причина всех проблем."
            ]
            joke = random.choice(jokes)
            self.send_message(chat_id, f"😂 {joke}")
        
        elif text == "/stats":
            msg_count = self.db.get_message_count(user_id)
            cmd_count = self.db.get_command_count(user_id)
            self.send_message(chat_id, f"📊 Твоя статистика:\n💬 Сообщений: {msg_count}\n⚡ Команд: {cmd_count}")
        
        elif text == "/info":
            self.send_message(chat_id, "🤖 Бот для демонстрации SonarQube\n📦 Версия: 1.0.0\n🐍 Python + Telegram API")
        
        # ОПАСНО! eval() - это SECURITY VULNERABILITY
        elif text.startswith("/calc "):
            expression = text[6:].strip()
            if expression:
                try:
                    # НИКОГДА НЕ ИСПОЛЬЗУЙ eval() в реальном коде!
                    result = eval(expression)  # <--- SECURITY VULNERABILITY
                    self.send_message(chat_id, f"🧮 Результат: {result}")
                except Exception as e:
                    self.send_message(chat_id, f"❌ Ошибка: {str(e)}")
            else:
                self.send_message(chat_id, "Пример: /calc 2+2")
        
        elif text.startswith("/echo "):
            echo_text = text[6:].strip()
            if echo_text:
                self.send_message(chat_id, f"🔊 {echo_text}")
            else:
                self.send_message(chat_id, "Что повторить?")
        
        # МАГИЧЕСКИЕ ЧИСЛА (100, 5) - это CODE SMELL
        else:
            if len(text) > 100:
                self.send_message(chat_id, "📝 Слишком длинное сообщение, я устал читать 😴")
            elif random.randint(1, 5) == 1:
                self.send_message(chat_id, "🤔 Интересно...")
            else:
                self.send_message(chat_id, f"Ты написал: {text}")
        
        self.db.increment_commands(user_id)
    
    def run(self):
        print("🤖 Бот запущен...")
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
# ТОЧКА ВХОДА
# ============================================
if __name__ == "__main__":
    db = Database(DATABASE_NAME)
    db.connect()
    bot = TelegramBot(BOT_TOKEN, db)
    
    try:
        bot.run()
    finally:
        db.close()