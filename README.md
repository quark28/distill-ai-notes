# Distill AI: Умный помощник для заметок с сжатием RAG-контекста

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---
Telegram-бот, который не просто ищет ответы в заметках, но **сжимает извлечённый контекст**, оставляя только самую суть. Это позволяет:
- Сократить длину промптов;
- Ускорить ответы;
- Снизить затраты на API;
- Повысить точность ответов, удаляя "шум" из контекста.

---

## 🧠 Что внутри

- **Загрузка и индексация** документов (PDF, TXT, DOCX, XLSX, CSV);
- **Семантический поиск** по заметкам с помощью **Sentence Transformers** и векторной БД **ChromaDB**;
- **Сжатие контекста** (алгоритмы: суммаризация, извлечение ключевых предложений, ранжирование по релевантности);
- **Генерация ответа** через **Mistral API** на основе сжатого контекста;
- **Telegram-бот** (aiogram) и **Desktop Dashboard** на Tkinter для мониторинга;
- **Экспериментальный модуль** для сравнения метрик: точность, длина промпта, время ответа.

---

## 🛠 Технологический стек

- **Язык:** Python 3.10+
- **Векторная БД:** ChromaDB
- **Эмбеддинги:** Sentence Transformers
- **LLM:** Mistral API
- **Telegram:** aiogram
- **GUI:** Tkinter
- **Сжатие:** кастомный алгоритм

---

## 🚀 Установка и запуск

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/yourusername/distill-ai-notes.git
cd distill-ai-notes
```

### 2. Создайте и активируйте виртуальное окружение
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Установите зависимости
```bash
pip install -r requirements.txt
```

### 4. Создайте файл `.env` с ключами
```bash
TELEGRAM_TOKEN=your_telegram_bot_token
MISTRAL_API_KEY=your_mistral_api_key
```

### 5. Запустите проект
```bash
python main.py
```
---

## 📄 Лицензия

Проект распространяется под лицензией MIT.
