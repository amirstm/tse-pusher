FROM python:3.12

ENV TZ="Asia/Tehran"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /python-code
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir tsetmc-pusher
COPY main_server.py .

ENV WEBSOCKET_HOST localhost
ENV WEBSOCKET_PORT 8765 

EXPOSE $websocket_port

CMD ["python", "main_server.py"]