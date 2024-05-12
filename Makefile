# TODO: Add commands to be compatible for windows
# TODO: Add commands for tesk_api

# Define variables
PYTHON_CMD := $(shell command -v python3 2> /dev/null)
BUILDAH_CMD := $(shell command -v buildah 2> /dev/null)
DOCKER_CMD := $(shell command -v docker 2> /dev/null)
POETRY_CMD := $(shell command -v poetry 2> /dev/null)
ELIXIR_CLOUD_REGISTRY := docker.io/elixircloud
DOCKER_FILE_PATH := deployment/containers

# Define arguments
IMAGE ?= filer
TAG ?= testing

default: help

# Help message
.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo "Available targets:"
	@echo "	\033[1mvenv \033[37m(v\033[0m)"
	@echo "		\033[36mCreate virtual environment\033[0m"
	@echo "	\033[1mclean-venv \033[37m(cv\033[0m)"
	@echo "		\033[36mRemove virtual environment\033[0m"
	@echo "	\033[1mclean-dot \033[37m(cd\033[0m)"
	@echo "		\033[36mRemove dot generated cache dirs\033[0m"
	@echo "	\033[1minstall \033[37m(i\033[0m)"
	@echo "		\033[36mInstall dependencies\033[0m"
	@echo "	\033[1mformat-lint \033[37m(fl\033[0m)"
	@echo "		\033[36mFormats and lints python files\033[0m"
	@echo "	\033[1mbuild-service-image \033[37m(bsi\033[0m)"
	@echo "		\033[36mBuild image for service (tesk_core)\033[0m"
	@echo "		\033[36mEg: make bsi IMAGE=filer TAG=1.1.0\033[0m"
	@echo "	\033[1mbuild-service-image-all \033[37m(bsia\033[0m)"
	@echo "		\033[36mBuild images for all services\033[0m"
	@echo "	\033[1mrun-service\033[0m"
	@echo "		\033[36mRun container for service (tesk_core)\033[0m"
	@echo "		\033[36mEg: make run-service IMAGE=filer TAG=testing\033[0m"
	@echo "	\033[1mclean-service-image \033[37m(csi\033[0m)"
	@echo "		\033[36mClean image for service (tesk_core)\033[0m"
	@echo "		\033[36mEg: make csi IMAGE=filer TAG=testing\033[0m"
	@echo "	\033[1mclean-service-image-all \033[37m(csia\033[0m)"
	@echo "		\033[36mClean images for all services of the given tag\033[0m"
	@echo "		\033[36mEg: make csia TAG=testing\033[0m"
	@echo "	\033[1mhelp\033[0m"
	@echo "		\033[36mDisplay this help message\033[0m"

.PHONY: venv
venv:
	@if [ -x "$(PYTHON_CMD)" ]; then \
		$(PYTHON_CMD) -m venv .venv; \
		echo "🙏 Virtual environment created. To activate, run:"; \
		echo "source .venv/bin/activate"; \
	else \
		echo "🐍 Please install `python3` to create virtual environment."; \
		exit 1; \
	fi

.PHONY: v
v: venv

.PHONY: clean-venv
clean-venv:
	rm -rf .venv

.PHONY: cv
cv: clean-venv

.PHONY: clean-dot
clean-dot:
	rm -rf .venv .mypy_cache .pytest_cache .coverage .ruff .ruff_cache .eggs __pycache__/
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: cd
cd: clean-dot

.PHONY: install
install:
	@if [ -x "$(POETRY_CMD)" ]; then \
		poetry install; \
	else \
		echo "🔏 Install poetry."; \
	fi

.PHONY: i
i: install

.PHONY: format-lint
format-lint:
	@if [ -f .venv/bin/ruff ]; then \
		ruff format; \
		ruff check; \
	else \
		echo "⬇️ Install deps, create venv using 'make v' and install using `make i`."; \
	fi

.PHONY: fl
fl: format-lint

.PHONY: build-service-image
build-service-image:
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
		echo "🐳 Please install buildah or docker to build images."; \
		exit 1; \
	fi

.PHONY: bsi
bsi: build-service-image

.PHONY: build-service-image-all
build-service-image-all:
	@make build-service-image IMAGE=filer TAG=$(TAG)
	@make build-service-image IMAGE=taskmaster TAG=$(TAG)

.PHONY: bsia
bsia: build-service-image-all

.PHONY: run-service
run-service:
	@if [ -x "$(DOCKER_CMD)" ]; then \
		$(DOCKER_CMD) run \
			-it --rm $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG); \
	else \
		echo "🐳 Please install docker to run images."; \
		exit 1; \
	fi

.PHONY: clean-service-image 
clean-service-image:
		@if [ -x "$(BUILDAH_CMD)" ]; then \
				if $(BUILDAH_CMD) inspect $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG) > /dev/null 2>&1; then \
						$(BUILDAH_CMD) rmi $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG); \
				else \
						echo "🔍 Image $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG) not found."; \
				fi \
		elif [ -x "$(DOCKER_CMD)" ]; then \
				if $(DOCKER_CMD) inspect $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG) > /dev/null 2>&1; then \
						$(DOCKER_CMD) rmi $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG); \
				else \
						echo "🔍 Image $(ELIXIR_CLOUD_REGISTRY)/tesk-core-$(IMAGE):$(TAG) not found."; \
				fi \
		else \
				echo "🐳 Please install buildah or docker to clean images."; \
				exit 1; \
		fi

.PHONY: csi
csi: clean-service-image

.PHONY: clean-service-image-all
clean-service-image-all:
	@make clean-service-image IMAGE=filer TAG=$(TAG)
	@make clean-service-image IMAGE=taskmaster TAG=$(TAG)

.PHONY: csia
csia: clean-service-image-all