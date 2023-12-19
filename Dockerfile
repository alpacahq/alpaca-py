# Install dependencies only when needed
FROM python:3.11 AS deps

ARG POETRY_VERSION=1.6.1
ENV POETRY_VERSION ${POETRY_VERSION}

RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Build the docs
FROM deps AS builder

WORKDIR /app

COPY . .

# for the config line below, see https://github.com/python-poetry/poetry/issues/7611#issuecomment-1747836233 (can be dropped with poetry >= 1.7.0)
RUN poetry config installer.max-workers 1
RUN poetry install

WORKDIR /app/docs

RUN poetry run make html

# Serve static files
FROM nginx:alpine

# COPY ./nginx.conf /etc/nginx/nginx.conf

COPY --from=builder /app/docs/_build/html /usr/share/nginx/html

ENTRYPOINT ["nginx", "-g", "daemon off;"]
