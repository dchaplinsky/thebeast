FROM python:3.9.15-bullseye

WORKDIR /usr/src/thebeast

COPY requirements.txt ./

RUN pip install --no-binary=:pyicu: pyicu \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install black