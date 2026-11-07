FROM python:3.11-slim
WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY dbt ./dbt
COPY src ./src
RUN pip install --no-cache-dir ".[warehouse,ml]"
RUN mkdir -p /workspace/dbt/logs /workspace/dbt/target \
    && chown -R 10001:0 /workspace/dbt/logs /workspace/dbt/target
USER 10001
ENTRYPOINT []
