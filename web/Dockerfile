FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py config.py api_client.py ./
COPY templates ./templates
COPY static ./static

RUN mkdir -p image_pool

EXPOSE 5000

CMD ["python", "app.py"]
