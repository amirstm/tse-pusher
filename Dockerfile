FROM python:3.12

WORKDIR /python-code
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir tsetmc-pusher
COPY main_server.py .

EXPOSE 8765

CMD ["python", "main_server.py"]