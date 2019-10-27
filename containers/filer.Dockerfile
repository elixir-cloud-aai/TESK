# Builder: produce wheels

FROM alpine:3.10 as builder

RUN apk add --no-cache python3
RUN apk add --no-cache git
RUN python3 -m pip install --upgrade setuptools pip wheel

WORKDIR /app/
COPY . .

RUN python3 setup.py bdist_wheel

# Install: copy tesk-core*.whl and install it with dependencies

FROM alpine:3.10

RUN apk add --no-cache python3

COPY --from=builder /app/dist/tesk*.whl /root/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir /root/tesk*.whl

ENTRYPOINT ["filer"]
