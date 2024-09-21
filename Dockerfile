FROM python:3.8 AS builder
WORKDIR /usr/src/app
COPY . /usr/src/app
ADD requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt --timeout 10000
ADD main.py /
ENV PYTHONUNBUFFERED=1
ENV PYTHONASYNCIODEBUG=1
RUN apt-get update && apt install ffmpeg -y
CMD [ "python", "./main.py" ]
