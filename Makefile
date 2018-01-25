ECR_REPO=698514710897.dkr.ecr.us-west-1.amazonaws.com
APP_NAME=backend

##########################      AWS / PRODUCTION      ##########################

# Authenticate Docker client
ecr-login:
	$(shell aws ecr get-login --no-include-email --region us-west-1)

# Build backend image
build:
	docker build ./python_app -t mappening/$(APP_NAME)

# Login, build, and push latest image to AWS
push: ecr-login build
	docker tag $(APP_NAME):latest $(ECR_REPO)/$(APP_NAME):latest
	docker push $(ECR_REPO)/$(APP_NAME):latest

##################       LOCAL DEVELOPMENT (Backend Only)     ################## 

# Build and run backend image
dev: build
	docker run --rm --name backend-dev -v $(shell pwd)/python_app:/app -p "5000:5000" -it mappening/$(APP_NAME)

# Stop running containers
stop:
	-docker ps | tail -n +2 | cut -d ' ' -f 1 | xargs docker kill
