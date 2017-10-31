build:
	docker-compose build

run: build
	docker-compose up

deploy:
	docker-compose up -d

stop:
	-sudo docker ps | tail -n +2 | cut -d ' ' -f 1 | xargs sudo docker kill

reset:
	-sudo docker ps -a | tail -n +2 | cut -d ' ' -f 1 | xargs sudo docker rm
	-sudo docker images | tail -n +2 | tr -s ' ' | cut -d ' ' -f 3 | xargs sudo docker rmi --force
