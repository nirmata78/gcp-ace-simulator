# The exam app and the read-only kb.py commands. LLM authoring stays on the venv path (see README).
# Refresh the digest with: docker buildx imagetools inspect python:3.12-slim
ARG BASE_IMAGE=python:3.12-slim@sha256:e695ab189fa2d082b1c61c69a6b888a5adeca61ceeccad107b1ed2a125721a9e

FROM ${BASE_IMAGE} AS builder
WORKDIR /build
COPY requirements.lock .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r requirements.lock

FROM ${BASE_IMAGE}
ARG ACE_VERSION=dev
LABEL org.opencontainers.image.title="gcp-ace-simulator" \
      org.opencontainers.image.version="${ACE_VERSION}" \
      org.opencontainers.image.source="https://github.com/nirmata78/gcp-ace-simulator" \
      org.opencontainers.image.licenses="MIT"

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app.py VERSION LICENSE ./
COPY .streamlit ./.streamlit
COPY src ./src
COPY scripts/kb.py scripts/check_network.py ./scripts/
COPY data/sections ./data/sections
COPY data/register.json ./data/register.json

# Created before VOLUME, so a new named volume inherits the non-root owner.
# chmod: COPY keeps host modes, and a clone made under a strict umask would be unreadable to that user.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin ace \
    && mkdir /state && chown ace:ace /state \
    && chmod -R a+rX /app

ENV PATH="/opt/venv/bin:$PATH" \
    ACE_STATE_DIR=/state \
    HOME=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER 10001
VOLUME /state
EXPOSE 8501

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2)"]

# Listens on every interface inside the container. Publish it to 127.0.0.1 only: the app has no authentication.
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--server.fileWatcherType=none", "--browser.serverAddress=localhost"]
