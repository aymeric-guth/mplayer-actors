FROM ubuntu:kinetic-20220602 as builder
RUN apt update && apt-get install -y \
  alsa-utils \
  libasound2 \
  libasound2-plugins \
  pulseaudio \
  pulseaudio-utils \
  python3 \
  python3-pip \
  mpv \
  libmpv-dev \
  --no-install-recommends
RUN apt install -y ffmpeg
RUN apt install -y libavcodec-dev
RUN apt install -y libavcodec-dev
RUN apt install -y libavutil-dev
RUN apt install -y libswresample-dev
RUN apt install -y build-essential
RUN apt install -y pkg-config
RUN apt install -y python3
RUN apt install -y python3-pip
RUN apt install -y libmpv-dev
RUN apt install -y nano
RUN apt install -y git
RUN apt install -y netcat-openbsd
RUN rm -rf /var/lib/apt/lists/*


FROM builder as stagging
ENV HOME /home/pulseaudio
ENV PULSE_SERVER=host.docker.internal
RUN useradd -u 501 --create-home --home-dir $HOME pulseaudio \
  && usermod -aG audio,pulse,pulse-access pulseaudio \
  && chown -R pulseaudio:pulseaudio $HOME
RUN mkdir -p /home/pulseaudio/.av-mp/mount_point
WORKDIR $HOME
# RUN git clone https://git.ars-virtualis.org/yul/flux.git
WORKDIR ${HOME}/flux
COPY ./src ./src
COPY ./requirements.txt ./requirements.txt
RUN chown -R pulseaudio:pulseaudio /home/pulseaudio
USER pulseaudio
RUN python3 -m pip install -r requirements.txt


FROM stagging AS runtime
# ENTRYPOINT [ "python3", "-m", "src" ]
