FROM docker.openmodelica.org/build-deps

COPY . /app

WORKDIR /app

RUN apt-get update \
  && apt-get install -qy gnupg wget ca-certificates apt-transport-https sudo \
  && echo "deb https://build.openmodelica.org/apt `lsb_release -sc`  release" > /etc/apt/sources.list.d/openmodelica.list \
  && wget https://build.openmodelica.org/apt/openmodelica.asc -O- | apt-key add - \
  && apt-get update \
  && apt-get install -qy --no-install-recommends omc \
  && apt-get install -qy --no-install-recommends omc omlib-modelica-3.2.2 \
  && rm -rf /var/lib/apt/lists/* \
  && python -m pip install -U . \
  && chmod a+rwx -R /app

ENTRYPOINT [ "python3" ]

CMD [ "OMWebService/app.py" ]
