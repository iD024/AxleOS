
# Sets up the OS and insatlls Python 3.10
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3.10 /usr/bin/python


# Sets up beamng.tech
WORKDIR /app

#Here we need to download BeamNG.tech zip file for linux
# place it MANUALLY in the same folder as this Dockerfile

ARG BEAMNG_TECH_VERSION=0.31.0.0
COPY BeamNG.tech.${BEAMNG_TECH_VERSION}.zip .

RUN unzip BeamNG.tech.${BEAMNG_TECH_VERSION}.zip && \
    rm BeamNG.tech.${BEAMNG_TECH_VERSION}.zip



# Installs Python dependencies
COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src


# THIS IS MAIN CMD which will run things
ENTRYPOINT ["python", "-u", "src/run_simulation.py"]