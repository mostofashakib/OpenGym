ROOT:=$(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
IMAGE_NAME=webshites-gmail
DOCKERFILE:=$(ROOT)/containers/gmail/Dockerfile
CONTEXT:=$(ROOT)

# Controls
HOST_PORT?=80
CONTAINER_NAME?=gmail
SEED_SEED?=gmail
SEED_THREADS?=8
SEED_SINGLES?=12
SEED_MAX_MESSAGES_PER_THREAD?=4

.PHONY: build run run-seeded seed bash stop clean

build:
	docker build -f $(DOCKERFILE) -t $(IMAGE_NAME):latest $(CONTEXT)

run: build
	docker run --rm --name $(CONTAINER_NAME) -p $(HOST_PORT):80 $(IMAGE_NAME):latest

run-seeded: build
	docker run --rm --name $(CONTAINER_NAME) -p $(HOST_PORT):80 \
	  -e SEED_ON_STARTUP=true \
	  -e SEED_SEED=$(SEED_SEED) \
	  -e SEED_THREADS=$(SEED_THREADS) \
	  -e SEED_SINGLES=$(SEED_SINGLES) \
	  -e SEED_MAX_MESSAGES_PER_THREAD=$(SEED_MAX_MESSAGES_PER_THREAD) \
	  $(IMAGE_NAME):latest

seed:
	@docker exec $(CONTAINER_NAME) bash -lc 'scripts/generate_rand_state/generate_state.sh --url http://127.0.0.1:80 --path /api/state --verbose' || \
	  (echo "Container '$(CONTAINER_NAME)' not running. Start with 'make run' or 'make run-seeded' first." && false)

bash:
	docker exec -it $(CONTAINER_NAME) bash

stop:
	docker stop $(CONTAINER_NAME) || true

clean:
	docker rmi $(IMAGE_NAME):latest || true

