FROM python:3.12-slim-bookworm
ARG ALIST_VERSION=v3.65.0
ARG ALIST_SHA256=3ae71bf87d47d605ed86a2f3f32b57c7268742b9a5f68d6e545e2563d01c2af5
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -fsSL "https://github.com/AlistGo/alist/releases/download/${ALIST_VERSION}/alist-linux-amd64.tar.gz" -o /tmp/alist.tar.gz \
    && echo "${ALIST_SHA256}  /tmp/alist.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/alist.tar.gz -C /usr/local/bin alist \
    && chmod 755 /usr/local/bin/alist \
    && rm -rf /tmp/alist.tar.gz /var/lib/apt/lists/* \
    && useradd -m -u 1000 user
WORKDIR /app
COPY --chown=user:user bootstrap.py upload-ui.html /app/
USER user
ENV ALIST_DATA_DIR=/home/user/alist-data ALIST_BINARY=/usr/local/bin/alist PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["python", "/app/bootstrap.py"]
