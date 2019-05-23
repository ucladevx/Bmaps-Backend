# Takes around 15-20 minutes to run the first time (depending on your computer)
FROM mappening/base

# Install the rest of the packages
COPY requirements.txt /tmp
RUN cd /tmp && pip3 install -r requirements.txt

WORKDIR /app
COPY . .
RUN ls -l

EXPOSE 5000
CMD ["python3", "app.py"]
