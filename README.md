# distill-ai-notes

RAG Telegram-бот для личной базы знаний с кастомным препроцессингом контекста перед отправкой в LLM.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Как это работает

Стандартный RAG-пайплайн дополнен шагом компрессии контекста перед сборкой промпта:
Заметка → ChromaDB (rubert-tiny2) → semantic search → compressor.py → Mistral API → ответ

**compressor.py** обрабатывает каждый найденный чанк через spaCy (`ru_core_news_sm`):
- Убирает стоп-слова и пунктуацию
- Оставляет только содержательные токены (NOUN, VERB, ADJ, ADV, PROPN, NUM)
- Редактирует чувствительные данные (пароли, токены) перед отправкой в API

Это сокращает длину промпта при сохранении ключевых сущностей.

**Эмбеддинги:** `cointegrated/rubert-tiny2` — русскоязычная модель, запускается локально через Sentence Transformers, данные не покидают машину.

---

## Возможности

- Индексация документов: PDF, TXT, DOCX, XLSX
- Семантический поиск по личной базе (изолированно по `user_id`)
- Пересылка сообщений напрямую в бот для индексации
- Поддержка прокси (настройка из GUI без перезапуска)
- Админ-панель на CustomTkinter: мониторинг пользователей, очистка данных, логи

---

## Стек

| Компонент | Технология |
|---|---|
| Бот | aiogram 3, FSM |
| Эмбеддинги | Sentence Transformers, rubert-tiny2 |
| Векторная БД | ChromaDB (persistent) |
| Препроцессинг | spaCy ru_core_news_sm |
| LLM | Mistral API (mistral-small) |
| GUI | CustomTkinter |

---

## Структура
distill-ai-notes/

├── core/

│   ├── compressor.py    # POS-фильтрация + редактирование секретов

│   ├── llm.py           # Mistral-клиент, сборка промпта

│   └── vector_store.py  # ChromaDB wrapper, rubert-tiny2 эмбеддинги

├── data/chroma/         # Персистентная векторная БД

├── gui.py               # CustomTkinter dashboard

├── main.py              # aiogram bot, FSM, document extraction

└── requirements.txt

---

## Установка

```bash
git clone https://github.com/quark28/distill-ai-notes.git
cd distill-ai-notes

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download ru_core_news_sm
```

Создайте `.env`:
TELEGRAM_TOKEN=your_token

MISTRAL_API_KEY=your_key

PROXY_URL=your_proxy  # опционально

Запуск:

```bash
python main.py
```

---

## Лицензия

MIT