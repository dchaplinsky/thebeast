FROM python:3.13-bookworm

WORKDIR /usr/src/thebeast

COPY ./requirements.txt ./

RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y libicu-dev python3-icu pkg-config curl

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
 && apt-get install -y libyajl-dev \
 && pip install --no-binary :all: yajl \
 && export PATH="$HOME/.cargo/bin:$PATH" \
 && . ~/.bashrc \
 && rustup update
 
RUN pip install --upgrade pip \
 && pip install --no-binary=:pyicu: pyicu \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install black