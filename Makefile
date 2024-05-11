# TODO: Add commands to be compatible for windows
# TODO: Add commands for tesk_api

# Define variables
PYTHON_CMD := $(shell command -v python3 2> /dev/null)
BUILDAH_CMD := $(shell command -v buildah 2> /dev/null)
DOCKER_CMD := $(shell command -v docker 2> /dev/null)
ELIXIR_CLOUD_REGISTRY := docker.io/elixircloud
DOCKER_FILE_PATH := deployment/containers

# Define arguments
IMAGE ?= filer
TAG ?= testing

# Default target, build image if `make` is called without any arguments
default: build

# Create and activate virtual environment
.PHONY: venv
venv:
	@if [ -x "$(PYTHON_CMD)" ]; then \
		$(PYTHON_CMD) -m venv .venv; \
		echo "Virtual environment created. To activate, run: source .venv/bin/activate"; \
	else \
		echo "Please install python3 to create virtual environment."; \
		exit 1; \
	fi

# Remove virtual environment
.PHONY: clean-venv
clean-venv:
	rm -rf .venv

# TODO: Install package manages and change the below commands
# Install dependencies
.PHONY: install
install:
	@if [ -f .venv/bin/activate ]; then \
		pip install .; \
	else \
		echo "Virtual environment not found. Please create it first using 'make venv'."; \
	fi

# Build image
.PHONY: build
build:
	@if [ -x "$(BUILDAH_CMD)" ]; then \
		$(BUILDAH_CMD) bud \
			-t $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG) \
			--format=docker \
			--no-cache \
			-f $(DOCKER_FILE_PATH)/$(IMAGE).Dockerfile; \
	elif [ -x "$(DOCKER_CMD)" ]; then \
		$(DOCKER_CMD) build \
			-t $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG) \
			-f $(DOCKER_FILE_PATH)/$(IMAGE).Dockerfile .; \
	else \
		echo "Please install buildah or docker to build images."; \
		exit 1; \
	fi

# Run image
.PHONY: run
run:
	@if [ -x "$(DOCKER_CMD)" ]; then \
		$(DOCKER_CMD) run \
			-it --rm $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG); \
	else \
		echo "Please install docker to run images."; \
		exit 1; \
	fi

# Clean up built images or other generated artifacts
clean:
	docker rmi $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG)
