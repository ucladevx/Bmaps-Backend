# start with a lightweight linux image
FROM alpine:3.6

# add necessary packages
RUN apk update && \
    apk upgrade && \
    apk add bash curl nginx && \
    rm -rf /var/cache/apk/*

# create working directory
VOLUME ["/app"]
RUN mkdir -p /run/nginx

# copy data to app location
COPY nginx.conf /etc/nginx

# set the working directory and copy source files
WORKDIR /app

# open a port and start the server
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
