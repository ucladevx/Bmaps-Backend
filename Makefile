ECR_REPO=698514710897.dkr.ecr.us-west-1.amazonaws.com
APP_NAME=backend

ecr-login:
	$(shell aws ecr get-login --no-include-email --region us-west-1)

build:
	docker build . -t mappening/$(APP_NAME)

push: ecr-login build
	docker tag $(APP_NAME):latest $(ECR_REPO)/$(APP_NAME):latest
	docker push $(ECR_REPO)/$(APP_NAME):latest
