RUNNER?=USER

# Include Environment Variables from .env file if run as user
ifeq ($(RUNNER), USER)
	include .env
endif

##################       LOCAL DEVELOPMENT (Backend Only)     ##################

# Build backend image. Must be built before dev work (and only once unless changed)
build-base:
	docker build ./src -t $(BASE_NAME) -f $(BASE_DOCKERFILE)

# Run backend in dev mode with local Postgres database
dev:
	docker-compose -f $(DEV_DOCKER_COMPOSE) up --build

# Run backend in prod mode with AWS Postgres database
prod:
# Needed to be able to use docker-compose, since that relies on our base image.
# If we're running this as a user, then we've already built it as part of the initial repo installation
ifeq ($(RUNNER), GITHUB)
	make build-base
endif
	docker-compose up --build

# Stops the stack. Can also Ctrl+C in the same terminal window stack was run.
stop:
	docker-compose down

# Kill any running containers
kill:
	-docker ps | tail -n +2 | cut -d ' ' -f 1 | xargs docker kill

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
