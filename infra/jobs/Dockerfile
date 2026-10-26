FROM python:3.11-slim
WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY dbt ./dbt
COPY src ./src
RUN pip install --no-cache-dir ".[warehouse,ml]"
USER 10001
ENTRYPOINT []
