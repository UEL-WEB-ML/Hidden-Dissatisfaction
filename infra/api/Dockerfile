FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[api,db]"
RUN useradd --create-home --uid 10001 appuser && mkdir -p /var/lib/hidden-dissatisfaction/evidence && chown -R appuser:appuser /app /var/lib/hidden-dissatisfaction
USER appuser
EXPOSE 8000
CMD ["uvicorn", "hidden_dissatisfaction.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
