import os
import signal
import time
from multiprocessing import Process
from pathlib import Path

from streamlitgo.cli import main


def test_streamlit_run(capfd):
    import sys

    sys.argv = ["streamlitgo", "hello", "--server.headless", "true"]
    os.chdir(Path(__file__).parent)
    p = Process(target=main)
    p.start()
    time.sleep(5)
    # check stderr output contains "loading setup script at"
    captured = capfd.readouterr()
    try:
        assert "loading setup script at" in captured.err
    finally:
        # kill the process
        p.terminate()
        p.kill()
        p.join()


if __name__ == "__main__":
    test_streamlit_run()
