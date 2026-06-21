import os
import asyncio
import logging
import threading
from io import BytesIO

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

from pypdf import PdfReader
from docx import Document
import openpyxl

from core.vector_store import VectorStoreManager
from core.llm import ask_llm
from gui import ui_ctrl, run_gui

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Критическая ошибка: TELEGRAM_TOKEN не найден в .env")

logging.basicConfig(level=logging.ERROR)

dp = Dispatcher()

db = VectorStoreManager()
ui_ctrl.db_reference = db

try:
    existing_data = db.collection.get(include=["metadatas"])
    if existing_data and existing_data.get("metadatas"):
        unique_users = set()
        for meta in existing_data["metadatas"]:
            if meta and "user_id" in meta:
                unique_users.add(meta["user_id"])
        
        for user in unique_users:
            ui_ctrl.register_user_activity(user)
except Exception as e:
    print(f"[SYSTEM] Ошибка при загрузке пользователей из БД: {e}")

class NoteStates(StatesGroup):
    waiting_for_note = State()

async def extract_text_from_document(message: types.Message, bot: Bot) -> tuple[str | None, str]:
    try:
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_ext = file_name.split('.')[-1].lower()
        
        file = await bot.get_file(file_id)
        destination = BytesIO()
        await bot.download(file, destination=destination)
        destination.seek(0)
        
        if file_ext == 'txt':
            return destination.read().decode('utf-8', errors='ignore').strip(), file_name
        elif file_ext == 'pdf':
            reader = PdfReader(destination)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            return text.strip(), file_name
        elif file_ext == 'docx':
            doc = Document(destination)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text.strip(), file_name
        elif file_ext == 'xlsx':
            wb = openpyxl.load_workbook(destination, data_only=True)
            lines = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_str = " | ".join([str(cell) for cell in row if cell is not None])
                    if row_str.strip(): lines.append(row_str)
            return "\n".join(lines).strip(), file_name
        return None, file_name
    except Exception as e:
        ui_ctrl.log("ERROR", f"Extraction error: {e}")
        return None, "unknown"

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Добавить заметку")
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = str(message.from_user.id)
    ui_ctrl.register_user_activity(user_id)
    await message.answer("🧠 Привет! Я твой RAG-ассистент.", reply_markup=get_main_keyboard())

@dp.message(F.forward_date | F.forward_from | F.forward_from_chat)
async def handle_forwarded(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ui_ctrl.register_user_activity(user_id)
    
    text = message.text or message.caption or ""
    if message.document:
        text, _ = await extract_text_from_document(message, message.bot)
    
    if text:
        db.save_note(user_id, f"fwd_{message.message_id}", text)
        await message.answer("✅ Сохранено!")
    await state.clear()

@dp.message(F.text == "📝 Добавить заметку")
async def start_note(message: types.Message, state: FSMContext):
    await state.set_state(NoteStates.waiting_for_note)
    await message.answer("⏳ Пришлите текст или документ.")

@dp.message(NoteStates.waiting_for_note)
async def handle_note(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ui_ctrl.register_user_activity(user_id)
    
    text = message.text
    if message.document:
        text, _ = await extract_text_from_document(message, message.bot)
    
    if text:
        db.save_note(user_id, str(message.message_id), text)
        await message.answer("✅ Проиндексировано!")
    await state.clear()

@dp.message()
async def handle_question(message: types.Message):
    user_id = str(message.from_user.id)
    ui_ctrl.register_user_activity(user_id)
    
    query = message.text
    if not query: return
    
    context = db.search_notes(user_id=user_id, query=query, limit=6)
    if not context:
        await message.answer("В базе нет информации.")
        return
    
    answer = await asyncio.to_thread(ask_llm, query, context)
    await message.answer(answer)

async def run_bot():
    ui_ctrl.log("SYSTEM", "Bot service started.")
    
    while True:
        ui_ctrl.event_config_changed.clear()
        
        proxy = os.getenv("PROXY_URL")
        ui_ctrl.log("SYSTEM", f"Initializing bot (Proxy: {proxy})")
        
        timeout = 60
        
        try:
            session = AiohttpSession(proxy=proxy, timeout=timeout)
            bot = Bot(token=TELEGRAM_TOKEN, session=session)
            
            polling_task = asyncio.create_task(dp.start_polling(bot))
            
            while not ui_ctrl.event_config_changed.is_set():
                await asyncio.sleep(0.5)
                if polling_task.done():
                    break
            
            if not polling_task.done():
                polling_task.cancel()
                try: await polling_task
                except: pass
                ui_ctrl.log("SYSTEM", "Session closed for reconfiguration.")
            
            await bot.session.close()
            
        except Exception as e:
            ui_ctrl.log("ERROR", f"Initialization error: {e}")
            await asyncio.sleep(3)

def start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    run_gui(start_bot_thread)