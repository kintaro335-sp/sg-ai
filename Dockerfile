FROM python:3.10-slim

WORKDIR /app

RUN apt update

RUN apt install -y \
    ffmpeg
    # build-base \
    # pkgconf \
    # ffmpeg-dev \
    # ffmpeg \
    # ffmpeg-libavformat \
    # ffmpeg-libavcodec \
    # ffmpeg-libavdevice \
    # ffmpeg-libavutil \
    # ffmpeg-libavfilter \
    # ffmpeg-libswscale \
    # ffmpeg-libswresample

RUN pip install --upgrade cython

RUN python -m ensurepip --upgrade


COPY requirements.txt .

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "main.py"]
