FROM python:3.12.0

WORKDIR /python-code
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY main_server.py .

EXPOSE 8765

CMD ["python", "main_server.py"]