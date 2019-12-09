## Takes around 40-50 minutes to run the first time (depending on your computer)
FROM mappening/base

## Install the rest of the packages
COPY requirements.txt /tmp
RUN cd /tmp && pip3 install -r requirements.txt
COPY nginx/conf/nginx.conf /etc/nginx/nginx.conf
COPY uwsgi/conf/mappening.ini /etc/uwsgi/mappening.ini
COPY supervisord/conf/supervisord.conf /etc/supervisord.conf

## need to pre-initialize to stop problems finding nginx pid correctly on startup
RUN touch /var/run/nginx.pid

## Remove default nginx website
RUN rm -f /etc/nginx/sites-available/default
RUN rm -rf /usr/share/nginx/html/*

## Copy all backend files into container /app directory
WORKDIR /app
COPY . .

## Add a default user so we don't run as root and change the directories created
#  to be owned by this user
RUN addgroup -S bmaps && adduser -S bmapsdev -G bmaps
RUN chown -R bmapsdev:bmaps /app /tmp 


EXPOSE 5000

CMD ["supervisord"]
