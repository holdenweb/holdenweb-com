FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

# Install dependencies first so this layer is cached across code-only changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

ENV PYTHONUNBUFFERED=1
EXPOSE 8456

CMD ["uv", "run", "uwsgi", \
     "--http-socket", "0.0.0.0:8456", \
     "--wsgi-file", "wsgi.py", \
     "--master", "--processes", "2", "--threads", "2"]
