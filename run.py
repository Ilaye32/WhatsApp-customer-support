import sys
import asyncio
import selectors
import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config("api.app:app", host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(server.serve())
        finally:
            loop.close()
    else:
        asyncio.run(server.serve())
