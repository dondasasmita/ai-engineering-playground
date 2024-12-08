FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Cairo
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*


RUN pip install poetry

COPY ../pyproject.toml ../poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-dev

# CMD ["watchmedo", "auto-restart", "--directory=/app", "--pattern=*.py", "--recursive", "--", "poetry", "run", "python", "-m", "lsu_pilot.main"]
CMD ["poetry", "run", "python", "-m", "lsu_pilot.main"]