# syntax=docker/dockerfile:1.7-labs

###############################################
# Builder image: installs deps and runs tests.
###############################################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PIP_NO_CACHE_DIR=1

WORKDIR /src

# Prepare separate virtual environments for runtime and test dependencies.
RUN python -m venv /opt/venv && python -m venv /opt/testenv
ENV RUNTIME_VENV=/opt/venv
ENV TEST_VENV=/opt/testenv

COPY requirements.txt requirements-dev.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
	"${RUNTIME_VENV}/bin/pip" install --upgrade pip && \
	"${RUNTIME_VENV}/bin/pip" install -r requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
	"${TEST_VENV}/bin/pip" install --upgrade pip && \
	"${TEST_VENV}/bin/pip" install -r requirements.txt -r requirements-dev.txt

# Copy only the pieces that impact tests to keep cache hits high.
COPY app ./app
COPY tests ./tests
COPY pyproject.toml ./

# Run the full unit test suite before producing the runtime image.
ENV PATH="${TEST_VENV}/bin:$PATH"
RUN pytest -q
ENV PATH="${RUNTIME_VENV}/bin:$PATH"
RUN rm -rf "${TEST_VENV}"

###############################################
# Runtime image: minimal surface, hardened FS.
###############################################
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PATH="/opt/venv/bin:$PATH"

ARG APP_UID=10001
ARG APP_GID=10001
WORKDIR /app

RUN set -eux; \
	groupadd --system --gid "$APP_GID" recipe && \
	useradd --system --no-create-home --uid "$APP_UID" --gid "$APP_GID" recipe

COPY --from=builder /opt/venv /opt/venv
COPY app ./app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD \
	["python", "-c", "import sys,urllib.request,urllib.error;\ntry:\n    urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)\nexcept Exception:\n    sys.exit(1)"]

USER recipe

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
