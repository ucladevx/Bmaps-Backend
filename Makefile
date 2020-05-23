# Include Environment Variables from .env file
include .env
include ../.env

whoami := $(shell whoami)
basecheck := $(shell docker images $(BASE_NAME) | grep $(BASE_NAME))

##################       LOCAL DEVELOPMENT (Backend Only)     ##################

# Build backend image. Must be built before dev work (and only once unless changed)
# This command is being deprecated in favor of AWS ECR pulling
build-base:
	docker build --no-cache ./src -t $(BASE_NAME):$(whoami) -f $(BASE_DOCKERFILE)

build-dev:
	docker build ./src -f $(DEV_DOCKERFILE)

pull-base: ecr-login
	docker pull $(ECR_URI)/$(BASE_NAME):latest
	docker tag $(ECR_URI)/$(BASE_NAME):latest $(BASE_NAME):latest

# Authenticate Docker client
ecr-login:
	$(shell aws ecr get-login --no-include-email --region $(AWS_REGION))

push-base: ecr-login
	docker tag $(BASE_NAME):latest $(ECR_URI)/$(BASE_NAME):$(whoami)
	docker push $(ECR_URI)/$(BASE_NAME):$(whoami)

# Run backend in dev mode with local Postgres database
dev:
	docker-compose -f $(DEV_DOCKER_COMPOSE) up --build

# Run backend in prod mode with AWS Postgres database
prod:
	docker-compose up --build

check-for-base:
	docker images $(BASE_NAME) | grep $(BASE_NAME) \
	 || echo "Base Dockerfile with image tag $(BASE_NAME) not found! \
	Please run 'make pull-base' to get it"

# Stops the stack. Can also Ctrl+C in the same terminal window stack was run.
stop:
	docker-compose down

# Kill any running containers
kill:
	-docker ps | tail -n +2 | cut -d ' ' -f 1 | xargs docker kill

clean:
	rm -rf *.pyc

##################           LOCAL POSTGRES DATABASE          ##################

# Sets CONTAINER_ID variable with ID of postgres container.
# := means CONTAINER_ID will only be set if output is non-empty.
# -q option for quiet output with only the container ID.
# -f option to filter by image name.
CONTAINER_ID := $(shell docker ps -qf "name=$(POSTGRES_IMAGE)")

# Dependency of `pg` target that requires CONTAINER_ID to be set.
check-id:
ifndef CONTAINER_ID
	$(error CONTAINER_ID is undefined. Try `docker ps` and modify POSTGRES_IMAGE in .env file.)
endif

# Connects to psql shell of Postgres container when running `dev` target.
pg: check-id
	docker exec -ti $(CONTAINER_ID) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# Zip current db data.
zip:
	cd ./database/; \
	zip -ru ./postgres.zip ./postgres/ -x *.DS_Store; \
	echo "To unzip and restore run: make restore"

# Restore saved data.
restore:
	cd ./database/; \
	-rm -r ./database/postgres/; \
	unzip -o ./postgres.zip
