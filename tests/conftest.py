import socket
import threading
import time

import pytest
import uvicorn

from gestion_lafab.app import create_app
from tests.fakes import ENV, FakePaheko


@pytest.fixture
def paheko() -> FakePaheko:
    return FakePaheko()


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server(paheko):
    """The application served on a free port, with the simulated Paheko."""
    port = free_port()
    app = create_app(dict(ENV), paheko.transport())
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not srv.started:
        if time.monotonic() > deadline:
            raise RuntimeError("server did not start")
        time.sleep(0.01)
    yield f"http://127.0.0.1:{port}"
    paheko.held = False
    srv.should_exit = True
    thread.join(timeout=10)
