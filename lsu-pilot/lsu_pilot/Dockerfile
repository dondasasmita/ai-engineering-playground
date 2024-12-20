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

COPY pyproject.toml poetry.lock ./

COPY lsu_pilot ./lsu_pilot

COPY embedding ./embedding

COPY processed ./processed

RUN poetry config virtualenvs.create false

RUN poetry install --no-dev

COPY scripts/app_entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh
