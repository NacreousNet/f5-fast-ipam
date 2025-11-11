FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8443
# Run with TLS in production using a reverse proxy or uvicorn with certs mounted
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8443", "--proxy-headers"]
