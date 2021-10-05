FROM ubuntu:focal
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update 

RUN apt -y install  dcmtk

RUN apt install -y python3-pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

CMD [ "python3", "main.py" ]
