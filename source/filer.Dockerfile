# Builder: produce wheels

FROM alpine:3.23 AS builder

RUN apk add --no-cache python3 py3-pip
RUN apk add --no-cache git
RUN python3 -m pip install --upgrade setuptools pip wheel build --break-system-packages

WORKDIR /app

RUN git clone https://github.com/elixir-cloud-aai/tesk-core.git

WORKDIR tesk-core

RUN python3 -m build --wheel && rm -rf dist/*.tar.gz

# Install: copy tesk-core*.whl and install it with dependencies

FROM alpine:3.23

RUN apk add --no-cache python3 py3-pip

COPY --from=builder /app/tesk-core/dist/tesk*.whl /root/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir /root/tesk*.whl --break-system-packages

USER 100

ENTRYPOINT ["filer"]
