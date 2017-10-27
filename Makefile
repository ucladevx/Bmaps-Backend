build:
	docker build -t mappening_backend .

run: build
	docker run -p 5000:5000 -i -t mappening_backend
