FROM ubuntu:24.04
RUN apt-get update
RUN apt install python3 python3-pip python3.12-venv -y

WORKDIR /app

# Copy script
COPY clearfake_clipboard_grabber.py .

# Install additional dependencies
RUN python3 -m venv /app/.venv
RUN /app/.venv/bin/pip install pytest-playwright
RUN /app/.venv/bin/playwright install-deps
RUN /app/.venv/bin/playwright install chromium-headless-shell

# Default entrypoint to run the script
ENTRYPOINT ["/app/.venv/bin/python", "clearfake_clipboard_grabber.py"]