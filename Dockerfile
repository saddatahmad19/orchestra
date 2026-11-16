FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY orchestra ./orchestra
COPY web ./web
RUN useradd --create-home --uid 10001 orchestra && mkdir -p /data && chown -R orchestra:orchestra /app /data
USER orchestra
EXPOSE 8080
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"
CMD ["uvicorn", "orchestra.main:app", "--host", "0.0.0.0", "--port", "8080"]
