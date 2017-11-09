ECR_REPO=698514710897.dkr.ecr.us-west-1.amazonaws.com
APP_NAME_FLASK=web_flask
APP_NAME_NGINX=web_nginx
EC2_IP=52.53.197.64

ecr-login:
	$(shell aws ecr get-login --no-include-email --region us-west-1)

build:
	docker build ./python_app -t $(APP_NAME_FLASK)
	docker build ./nginx_app -t $(APP_NAME_NGINX)
	# docker-compose build

run: build
	docker-compose up

push: ecr-login build
	docker tag $(APP_NAME_FLASK):latest $(ECR_REPO)/$(APP_NAME_FLASK):latest
	docker push $(ECR_REPO)/$(APP_NAME_FLASK):latest

	docker tag $(APP_NAME_NGINX):latest $(ECR_REPO)/$(APP_NAME_NGINX):latest
	docker push $(ECR_REPO)/$(APP_NAME_NGINX):latest

ssh:
	ssh ubuntu@$(EC2_IP) -i id_rsa_mappening.pem

deploy: ecr-login
	docker-compose pull
	docker-compose up

stop:
	-docker ps | tail -n +2 | cut -d ' ' -f 1 | xargs docker kill

reset:
	-docker ps -a | tail -n +2 | cut -d ' ' -f 1 | xargs docker rm
	-docker images | tail -n +2 | tr -s ' ' | cut -d ' ' -f 3 | xargs docker rmi --force
