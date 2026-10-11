# 64,000 rows fit comfortably in memory: plain Python, no cluster needed.
FROM python:3.12.14-slim

WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt pytest==9.1.1 \
    && rm /tmp/requirements.txt \
    && useradd --create-home analyst

ENV PYTHONPATH=/app/src \
    MPLCONFIGDIR=/tmp/matplotlib
USER analyst
