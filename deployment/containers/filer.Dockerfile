###################################################
#   Stage 1: Build wheel                           #
###################################################
FROM python:3.11-alpine AS builder

# Set work directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy source code
COPY . .

# Build wheel
RUN poetry build -f wheel

###################################################
#   Stage 2: Install wheel and create user        #
###################################################
FROM python:3.11-alpine AS runner

# Copy built wheel from the builder stage
COPY --from=builder /app/dist/*.whl /dist/

# Install the application with dependencies
RUN pip install /dist/*.whl

# Create a non-root user
RUN adduser -D -u 1000 filerUser

# Switch to the non-root user
USER filerUser

# Set the working directory
WORKDIR /app

# Entrypoint command
ENTRYPOINT ["filer"]
