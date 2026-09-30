# PHG HTML capture worker v2 (PHG-034). Railway: New Service -> this folder -> set the env vars in README.
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY capture.py worker.py ./
CMD ["python", "-u", "worker.py"]
