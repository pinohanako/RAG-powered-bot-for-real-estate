FROM python:latest

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r /requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONASYNCIODEBUG=1

RUN apt-get update && apt install ffmpeg -y

COPY . ./

CMD [ "python", "main.py" ]
