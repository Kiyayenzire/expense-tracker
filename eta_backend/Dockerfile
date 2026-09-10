FROM python:3.12-slim

ARG PYTHON_ENV=prod

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements ./requirements
RUN pip install --upgrade pip && \
    if [ "$PYTHON_ENV" = "test" ]; then pip install -r requirements/test.txt; else pip install -r requirements/prod.txt; fi

# Copy entrypoint script, strip CRLF line endings, and grant executable permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Copy the entire backend application source code into the container
COPY . /app

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]