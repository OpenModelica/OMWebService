# OMWebService
OpenModelica web service, queries via a REST API

## Dependencies

- [Python >= 3.8.5](https://www.python.org/)
- [Python setuptools](https://pypi.org/project/setuptools/)
- [OpenModelica >= 1.19.0](https://openmodelica.org)

## Build & Run instructions

### Option 1

Set environment variable `FLASK_ENV=development` for development environment.
Install the dependencies and then run the following commands,

```bash
$ cd /path/to/OpenModelica/OMWebService
$ python -m pip install -U .
$ python Service/app.py
```

### Option 2

Use the Dockerfile provided to run with docker,

```bash
$ cd /path/to/OpenModelica/OMWebService
$ docker build . -t openmodelica/omwebservice
$ docker run --user nobody -p 8080:8080 openmodelica/omwebservice
```

In your browser, open the URL http://localhost:8080/api/