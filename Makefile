build:
	docker-compose build

run: build
	docker-compose up

deploy:
	docker-compose up -d

stop:
	-docker ps | tail -n +2 | cut -d ' ' -f 1 | xargs docker kill

reset:
	-docker ps -a | tail -n +2 | cut -d ' ' -f 1 | xargs docker rm
	-docker images | tail -n +2 | tr -s ' ' | cut -d ' ' -f 3 | xargs docker rmi --force
