# 🤖 Customer Support AI Agent (WhatsApp)

An intelligent, multi-modal customer support agent built to handle inquiries on WhatsApp. It answers questions using your internal knowledge base, scrapes live product data, transcribes voice messages, and analyzes images — all while retaining conversation context per customer for a seamless support experience.

---

## ✨ Features

- 💬 **Text messaging** — Conversational AI responses via DeepSeek Chat
- 🖼️ **Image understanding** — Analyzes images sent by customers (damaged items, product labels, screenshots) using Google Gemini Vision
- 🎙️ **Voice message support** — Transcribes voice notes using Groq Whisper before passing to the agent
- 🧠 **Per-customer memory** — Persistent conversation history and long-term memory via MongoDB
- 📚 **Internal knowledge base** — Answers product & service questions from your private documents using Gemini File Search
- 🌐 **Web browsing** — Fetches real-time data from URLs using Firecrawl and Crawl4AI
- ⚡ **Async processing** — Messages handled in background tasks to avoid webhook timeouts
- 📊 **Observability** — Request tracing and monitoring with Logfire

---

## 🏗️ Architecture

```
WhatsApp Customer
      │
      ▼
WhatsApp Cloud API (Meta)
      │  POST /whatsapp/webhook
      ▼
FastAPI App (api/app.py)
      │
      ▼
Route Handler (api/routes/whatsapp.py)
      │
      ├── Text  ──────────────────────────────────────┐
      │                                               │
      ├── Image ──► download_whatsapp_image()         │
      │             └──► analyze_image() [Gemini]     │
      │                                               ▼
      └── Audio ──► download_whatsapp_audio()     run_agent()
                    └──► process_audio() [Groq]   [LangGraph + DeepSeek]
                                                       │
                                          ┌────────────┼────────────┐
                                          ▼            ▼            ▼
                                    knowledgebase  firecrawler  web_crawler
                                    [Gemini]       [Firecrawl]  [Crawl4AI]
                                          │
                                          ▼
                                  MongoDB (memory + checkpoints)
                                          │
                                          ▼
                              send_whatsapp_message() → Customer
```

---

## 🗂️ Project Structure

```
├── api/
│   ├── app.py                    # FastAPI app factory + Logfire instrumentation
│   ├── __init__.py
│   ├── routes/
│   │   ├── whatsapp.py           # Webhook handler (POST verify + POST receive)
│   │   └── __init__.py
│   └── services/
│       ├── whatsapp_messager.py  # Send messages, download media from WhatsApp API
│       └── audio_processor.py   # Audio format detection, PCM→WAV, Groq STT
├── main.py                       # LangGraph agent setup, run_agent(), CLI test loop
├── tools.py                      # LangChain tools: knowledgebase, firecrawler, web_crawler, analyze_image
├── run.py                        # Uvicorn entry point (Windows-compatible)
├── .env.example                  # Environment variable template
└── requirements.txt
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | DeepSeek Chat (via OpenAI-compatible API) |
| Agent Framework | LangGraph + LangChain |
| Vision | Google Gemini 2.5 Flash Lite |
| Embeddings | Google Gemini Embedding 2 |
| Speech-to-Text | Groq Whisper Large v3 |
| Knowledge Base | Gemini File Search |
| Web Scraping | Firecrawl, Crawl4AI |
| Memory & Checkpointing | MongoDB (langgraph-checkpoint-mongodb, langgraph-store-mongodb) |
| API Server | FastAPI + Uvicorn |
| Observability | Logfire |
| WhatsApp Integration | Meta WhatsApp Cloud API |

---

## 🧰 Agent Tools

| Tool | Purpose |
|---|---|
| `knowledgebase` | Searches your company's internal documents — product catalogues, FAQs, policies |
| `firecrawler` | Fast scraping of web pages (e.g., order status pages, tracking links) |
| `web_crawler` | Deep scraping with Crawl4AI for complex or dynamic pages |
| `analyze_image` | Extracts details from customer-sent photos — damage, labels, charts, branding |

---

## 📨 Message Types Supported

| Type | Handling |
|---|---|
| Text | Passed directly to the agent |
| Image | Downloaded → analyzed by Gemini Vision → description + caption sent to agent |
| Voice/Audio | Downloaded → format detected → transcribed by Groq Whisper → text sent to agent |
| Other (video, doc, etc.) | Customer receives an unsupported message notice |

---

## 🧠 Memory Architecture

Each customer's WhatsApp number gets its own isolated memory thread in MongoDB:

- **Short-term memory** — Full conversation history per `thread_id` (phone number) via `MongoDBSaver`
- **Long-term memory** — Semantic vector store via `MongoDBStore` with Gemini Embedding 2 (3072 dims) for cross-session recall

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ilaye32/WhatsApp-customer-support.git
cd WhatsApp-customer-support
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Fill in your `.env` file — see the section below for how to obtain each key.

### 5. Configure the knowledge base and system prompt

In `tools.py`, replace the placeholder with your Gemini File Search store name:

```python
file_search_store_names=["Your gemini file search store name here"]
```

In `main.py`, replace the system prompt placeholder with your agent's persona and instructions:

```python
SYSTEM_PROMPT = """Your system prompt here"""
```

---

## 🔑 Obtaining Your API Keys

### `GROQ_API_KEY`
- Sign up at [console.groq.com](https://console.groq.com) and create an API key.
- Used for voice message transcription (Whisper Large v3).

### `GOOGLE_API_KEY`
- Go to [Google AI Studio](https://aistudio.google.com/) or [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
- Create an API key with access to the **Generative Language API**.
- Used for image analysis, embeddings, and knowledge base file search.

### `DEEPSEEK_API_KEY`
- Register at [platform.deepseek.com](https://platform.deepseek.com/) and generate an API key.
- Used as the core reasoning LLM (`deepseek-chat`).

### `FIRECRAWL_API_KEY`
- Sign up at [firecrawl.dev](https://www.firecrawl.dev/) and get your key.
- Used by the `firecrawler` tool for fast web scraping.

### `MONGO_DB_URL`
- Use a MongoDB Atlas free cluster or self-hosted MongoDB.
- Two collections will be created automatically: `memory_store` and `thread_checkpoints`.
- Format: `mongodb+srv://<user>:<password>@cluster.mongodb.net/`

### WhatsApp Cloud API (Meta)

Get these three values from [developers.facebook.com](https://developers.facebook.com/):

1. Go to Meta for Developers, create an app, and add the **WhatsApp** product.
2. Under **WhatsApp > API Setup**, note your **Phone Number ID** and generate an access token.
3. Under **WhatsApp > Configuration**, set your webhook URL:
   ```
   https://your-domain.com/whatsapp/webhook
   ```
4. Set your **Verify Token** to any custom string — this must match `WHATSAPP_VERIFY_TOKEN` in your `.env`.
5. Subscribe to the **messages** webhook field.

| Variable | Where to find it |
|---|---|
| `WHATSAPP_API_TOKEN` | Permanent access token from your WhatsApp Business App |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone Number ID in WhatsApp > API Setup |
| `WHATSAPP_VERIFY_TOKEN` | A custom string you define during webhook setup |

### `LOGFIRE_TOKEN` *(optional)*
- Sign up at [logfire.pydantic.dev](https://logfire.pydantic.dev/) and generate a token.
- Leave blank if you don't need monitoring.

---

## 🚀 Running the Server

```bash
python run.py
```

The server starts on `http://0.0.0.0:8000`.

### Webhook endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/whatsapp/webhook` | WhatsApp webhook verification |
| `POST` | `/whatsapp/webhook` | Receive incoming WhatsApp messages |

> **Local development:** Use [ngrok](https://ngrok.com) to expose your local server to the internet:
> ```bash
> ngrok http 8000
> ```
> Then use the generated `https://` URL as your webhook in the Meta dashboard.

---

## 🧪 Local CLI Testing

Test the agent without WhatsApp using the built-in terminal loop:

```bash
python main.py
```

This starts an interactive session where you can chat with the agent directly from your terminal.

---

## 📋 Environment Variables Reference

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key — Whisper STT |
| `GOOGLE_API_KEY` | Google API key — Gemini Vision, Embeddings, File Search |
| `DEEPSEEK_API_KEY` | DeepSeek API key — main LLM |
| `FIRECRAWL_API_KEY` | Firecrawl API key — web scraping |
| `MONGO_DB_URL` | MongoDB connection string — memory & checkpoints |
| `WHATSAPP_API_TOKEN` | Meta WhatsApp Cloud API access token |
| `WHATSAPP_VERIFY_TOKEN` | Custom string for webhook verification |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID from Meta dashboard |
| `LOGFIRE_TOKEN` | Logfire token — observability (optional) |

---

## 📄 License

MIT License — feel free to use and adapt this project.
