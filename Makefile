# Include Environment Variables from .env file
include .env 

ECR_REPO=698514710897.dkr.ecr.us-west-1.amazonaws.com
BASE_NAME=mappening/base
APP_NAME=mappening/backend
DEV_NAME=mappening/dev
PROD_DOCKERFILE=./src/Dockerfile
BASE_DOCKERFILE=./src/Base-Dockerfile
DEV_DOCKER_COMPOSE=./docker-compose-dev.yml

##########################      AWS / PRODUCTION      ##########################

# Authenticate Docker client
ecr-login:
	$(shell aws ecr get-login --no-include-email --region us-west-1)

# Build backend image
build:
	docker build ./src -t $(APP_NAME)

# Login, build, and push latest image to AWS
push: ecr-login build
	docker tag $(APP_NAME):latest $(ECR_REPO)/$(APP_NAME):latest
	docker push $(ECR_REPO)/$(APP_NAME):latest

#############################      AWS / DEV      ##############################

# Build backend image for dora
build-dora:
	docker build ./src -t $(DEV_NAME):dora

# Login, build, and push latest image to AWS for dev testing
dora: ecr-login build-dora
	docker tag $(DEV_NAME):dora $(ECR_REPO)/$(DEV_NAME):dora
	docker push $(ECR_REPO)/$(DEV_NAME):dora

##################       LOCAL DEVELOPMENT (Backend Only)     ##################

# Build backend image
build-base:
	docker build ./src -t $(BASE_NAME) -f $(BASE_DOCKERFILE)

# Build backend image
build-dev:
	docker build ./src -t $(APP_NAME) -f $(DEV_DOCKERFILE)

# Build backend image
build-prod:
	docker build ./src -t $(APP_NAME) -f $(PROD_DOCKERFILE)

# Build and run backend image
dev: build-dev
	docker run --rm --name backend-dev -v $(shell pwd)/src:/app -p "5000:5000" -it $(APP_NAME)

prod: build-prod
	docker run --rm --name backend-dev -v $(shell pwd)/src:/app -p "5000:5000" -it $(APP_NAME)

# Stop running containers
stop:
	-docker ps | tail -n +2 | cut -d ' ' -f 1 | xargs docker kill

##################     			  IN PROGRESS: POSTGRES 			    ##################

up-dev:
	docker-compose up -f $(DEV_DOCKER_COMPOSE) --build

up-prod:
	docker-compose up --build

# Stops the stack. Can also Ctrl+C in the same terminal window stack was run.
down:
	docker-compose down

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
	docker exec -ti $(CONTAINER_ID) psql -U $(POSTGRES_USER)

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
