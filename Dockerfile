FROM python:3.12

WORKDIR /python-code
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir tsetmc-pusher
COPY main_server.py .

ENV websocket_host localhost
ENV websocket_port 8765 

EXPOSE $websocket_port

CMD ["python", "main_server.py"]