FROM python:3.11-slim

# Copy project
COPY . /app

# Create user and install deps
RUN useradd appuser \
    && chown -R appuser /app \
    && rm -fr /app/.venv \
    && mkdir /home/appuser \
    && chown appuser /home/appuser \
    && pip install --upgrade pip \
    && pip install uv

WORKDIR /app

# Use a non-root user from now on
USER appuser


# Sync dependencies
RUN uv sync

# Expose API port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
