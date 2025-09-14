FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (build-essential for any wheels, tk for pillow if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tk \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure private directory exists for CSV snapshots
RUN mkdir -p /app/media/private

EXPOSE 8000

CMD ["/bin/sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]

