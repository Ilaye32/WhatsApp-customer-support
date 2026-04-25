import os
import base64
from langchain.tools import tool
from firecrawl import Firecrawl
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


@tool
def knowledgebase(query: str) -> str:
    """Gets knowledge from the internal knowledge base about Clothes Stocklots BV."""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=["Your gemini file search store name here"]
                        )
                    )
                ]
            )
        )
        return response.text
    except Exception as e:
        return f"Information not available: {str(e)}"


@tool
async def web_crawler(url: str) -> str:
    """
    Advanced web scraper using Crawl4AI.
    Use only when firecrawl or knowledgebase is not enough.
    """
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(session_id="agent_session")

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            if result.success:
                markdown = getattr(result, 'markdown_v2', None)
                if markdown and hasattr(markdown, 'raw_markdown'):
                    return markdown.raw_markdown.strip()
                return (result.markdown or "No content extracted").strip()
            else:
                return f"Scrape failed: {result.error_message or 'Unknown error'}"
    except Exception as e:
        return f"Deep scrape error: {str(e)}"


firecrawl_client = Firecrawl(api_key=os.getenv('FIRECRAWL_API_KEY'))


@tool
def firecrawler(url: str) -> str:
    """
    Scrapes the text content of a website.
    Use this tool when you need to read a specific URL to gather real-time information.
    """
    try:
        response = firecrawl_client.crawl(
            url,
            limit=1,
            scrape_options={
                'formats': ['markdown'],
                'proxy': 'auto',
                'only_main_content': True
            }
        )
        return str(response)
    except Exception as e:
        return f"Error scraping the website: {str(e)}"


@tool
def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Analyzes an image using Gemini and returns a detailed description of its contents.
    Extracts text, data, charts, tables, or any visual information present.
    """
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                "Extract all text, data, and visual content from this image in full detail. "
                "If it contains a chart, table, or diagram, describe its structure and values precisely. "
                "If it shows a clothing item or product, describe the style, color, condition, and any visible labels or branding."
            ]
        )
        return response.text
    except Exception as e:
        return f"Image analysis failed: {str(e)}"
