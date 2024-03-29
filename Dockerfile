FROM docker.openmodelica.org/build-deps

COPY . /app

WORKDIR /app

RUN apt-get update \
  && apt-get install -qy gnupg wget ca-certificates apt-transport-https sudo \
  && echo "deb https://build.openmodelica.org/apt `lsb_release -sc`  release" > /etc/apt/sources.list.d/openmodelica.list \
  && wget https://build.openmodelica.org/apt/openmodelica.asc -O- | apt-key add - \
  && apt-get update \
  && apt-get install -qy --no-install-recommends omc \
  && rm -rf /var/lib/apt/lists/* \
  && python3 -m pip install -U . \
  && chmod a+rwx -R /app

ENV FLASK_ENV=development \
    DOCKER_APP=yes

ENTRYPOINT [ "python3" ]

CMD [ "Service/app.py" ]