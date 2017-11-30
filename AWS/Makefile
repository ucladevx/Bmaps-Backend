ECR_REPO=698514710897.dkr.ecr.us-west-1.amazonaws.com
APP_NAME_FLASK=web_flask
APP_NAME_NGINX=web_nginx
APP_NAME_NODE=web_node
EC2_IP=52.53.197.64

ecr-login:
	sudo $(shell /home/ubuntu/.local/bin/aws ecr get-login --no-include-email --region us-west-1)

build:
	docker build ./python_app -t $(APP_NAME_FLASK)
	docker build ./nginx_app -t $(APP_NAME_NGINX)
	docker build ./node_app -t $(APP_NAME_NODE)

run: build
	docker-compose up

push: ecr-login
	docker tag $(APP_NAME_FLASK):latest $(ECR_REPO)/$(APP_NAME_FLASK):latest
	docker push $(ECR_REPO)/$(APP_NAME_FLASK):latest

	docker tag $(APP_NAME_NGINX):latest $(ECR_REPO)/$(APP_NAME_NGINX):latest
	docker push $(ECR_REPO)/$(APP_NAME_NGINX):latest

	docker tag $(APP_NAME_NODE):latest $(ECR_REPO)/$(APP_NAME_NODE):latest
	docker push $(ECR_REPO)/$(APP_NAME_NODE):latest

deploy: ecr-login
	sudo docker-compose pull
	sudo docker-compose up
