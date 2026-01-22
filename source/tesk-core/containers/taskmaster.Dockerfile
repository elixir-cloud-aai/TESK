# Builder: produce wheels

FROM alpine:3.19 as builder

RUN apk add --no-cache python3 py3-pip
RUN apk add --no-cache git
RUN python3 -m pip install --upgrade setuptools pip wheel --break-system-packages

WORKDIR /app/
COPY . .

RUN python3 setup.py bdist_wheel

# Install: copy tesk-core*.whl and install it with dependencies

FROM alpine:3.19

RUN apk add --no-cache python3 py3-pip

COPY --from=builder /app/dist/tesk*.whl /root/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir /root/tesk*.whl --break-system-packages

RUN adduser --uid 100 -S taskmaster
USER 100

ENTRYPOINT ["taskmaster"]
