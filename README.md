# Customer Support AI Agent (WhatsApp)

An intelligent, multi-modal customer support agent built to handle inquiries on WhatsApp. It answers questions using your internal knowledge base, scrapes live product data, transcribes voice messages, and analyzes images — all while retaining conversation context for a seamless support experience.

## What It Does

This agent acts as a frontline support assistant for your business. It can:

- **Answer product & service questions** by searching your internal knowledge base (manuals, catalogues, FAQs).
- **Fetch real-time information** from your website or external sources using web scraping.
- **Understand images** sent by customers (e.g., screenshots, damaged items, competitors' products) and describe them in detail.
- **Transcribe voice messages** so customers can speak their issues naturally.
- **Maintain context** across conversations — it remembers previous chats with each customer to provide consistent support.
- **Handle high traffic** by processing messages asynchronously without slowing down responses.

## Architecture Overview

1. **FastAPI Server** (`run.py` → `api/app.py`)
   - Exposes `/whatsapp/webhook` for Meta’s WhatsApp Cloud API.
2. **Webhook Handler** (`api/routes/whatsapp.py`)
   - Receives text, image, or voice messages.
   - Downloads media, transcribes audio, and passes everything to the AI agent.
3. **Support Agent** (`main.py`)
   - Built with LangGraph’s `create_agent`.
   - Uses **DeepSeek Chat** as the core reasoning engine.
   - Equipped with four specialised tools:
     - `knowledgebase`: searches your private company documents (via Gemini file search).
     - `firecrawler`: scrapes web pages quickly through Firecrawl.
     - `web_crawler`: deep scraping with Crawl4AI for complex pages.
     - `analyze_image`: extracts details from images (product labels, damage, charts, etc.).
   - Stores conversation history per customer in MongoDB for contextual follow-ups.
4. **WhatsApp Messenger** (`api/services/whatsapp_messager.py`)
   - Sends replies and downloads media using the WhatsApp Graph API.

## Tools for Customer Support

| Tool            | Purpose                                                                 |
|-----------------|-------------------------------------------------------------------------|
| `knowledgebase` | Searches your company’s internal knowledge base for product details, stock info, policies, etc. |
| `firecrawler`   | Fetches live content from URLs (e.g., order status pages, tracking links). |
| `web_crawler`   | Handles more complex scraping needs (dynamic pages).                    |
| `analyze_image` | Describes photos sent by customers — damaged goods, sizing labels, competitor flyers, etc. |

## Getting the Required .env Variables

All configuration is stored in `.env`. Here’s how to obtain each key:

### 1. `GROQ_API_KEY`
- Sign up at [console.groq.com](https://console.groq.com)
- Create an API key.
- Used for voice message transcription.

### 2. `GOOGLE_API_KEY`
- Go to [Google AI Studio](https://aistudio.google.com/) or [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
- Create an API key with access to the **Generative Language API**.
- Used for: image analysis, embeddings, and knowledge base file search.

### 3. `DEEPSEEK_API_KEY`
- Register at [platform.deepseek.com](https://platform.deepseek.com/).
- Used as the main AI model (model `deepseek-chat`).

### 4. `FIRECRAWL_API_KEY`
- Sign up at [firecrawl.dev](https://www.firecrawl.dev/).
- Used by the `firecrawler` tool for fast web scraping.

### 5. `MONGO_DB_URL`
- A MongoDB connection string (e.g., from free Atlas cluster).
- Two collections will be created: `memory_store` and `thread_checkpoints`.

### 6. WhatsApp Cloud API (Meta)
Obtain these from **[developers.facebook.com](https://developers.facebook.com/)**.

- `WHATSAPP_API_TOKEN` – permanent access token from your WhatsApp Business App.
- `WHATSAPP_PHONE_NUMBER_ID` – Phone Number ID from the WhatsApp settings.
- `WHATSAPP_VERIFY_TOKEN` – a custom string you define (used during webhook setup).

**Steps:**
1. Go to [Facebook for Developers](https://developers.facebook.com/), create an app, and add the **WhatsApp** product.
2. Note the Phone Number ID and generate a temporary access token.
3. Set up a webhook (URL will be `https://your-domain.com/whatsapp/webhook`), using your own verify token.
4. Subscribe to the `messages` event.

### 7. `LOGFIRE_TOKEN` (Optional)
- Sign up at [logfire.sh](https://logfire.sh/) if you want monitoring. Leave empty otherwise.

## Installation

```bash
git clone [<[repo-url](https://github.com/Ilaye32/WhatsApp-customer-support.git))>]
cd WhatsApp-customer-support

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
