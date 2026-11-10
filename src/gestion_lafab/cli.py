import threading
import time
import webbrowser

import uvicorn

from gestion_lafab.app import create_app

HOST = "127.0.0.1"
PORT = 8000


def main() -> None:
    """Start the server and open the home page in the browser."""
    server = uvicorn.Server(uvicorn.Config(create_app(), host=HOST, port=PORT))

    def open_when_started() -> None:
        while not server.started:
            if server.should_exit:
                return
            time.sleep(0.05)
        webbrowser.open(f"http://{HOST}:{PORT}/")

    threading.Thread(target=open_when_started, daemon=True).start()
    try:
        server.run()
    except KeyboardInterrupt:
        pass  # Ctrl+C: uvicorn has already shut down cleanly.
