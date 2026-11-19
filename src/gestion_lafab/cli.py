import threading
import time
import webbrowser

import uvicorn

from gestion_lafab.app import create_app
from gestion_lafab.config import read_env

HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def main() -> None:
    """Start the server and open the home page in the browser."""
    port = int(read_env().get("PORT") or DEFAULT_PORT)
    server = uvicorn.Server(uvicorn.Config(create_app(), host=HOST, port=port))

    def open_when_started() -> None:
        while not server.started:
            if server.should_exit:
                return
            time.sleep(0.05)
        webbrowser.open(f"http://{HOST}:{port}/")

    threading.Thread(target=open_when_started, daemon=True).start()
    try:
        server.run()
    except KeyboardInterrupt:
        pass  # Ctrl+C: uvicorn has already shut down cleanly.
