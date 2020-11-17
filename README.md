# OMWebService
OpenModelica web service, queries via a REST API

## Dependencies

- [Python >= 3.8.5](https://www.python.org/)
- [OpenModelica >= 1.16.0](https://openmodelica.org)
- Required python packages are installed via requirements.txt

## Build & Run instructions

### Option 1

Install the dependencies and then run the following commands,

```bash
$ cd /path/to/OpenModelica/OMWebService
$ pip install -r requirements.txt
$ python app.py
```

In your browser, open the URL http://localhost:8888/api/

### Option 2

Use the Dockerfile provided to run with docker,

```bash
$ cd /path/to/OpenModelica/OMWebService
$ docker build . -t openmodelica/omwebservice
$ docker run --user nobody -p 8080:8080 openmodelica/omwebservice
```

In your browser, open the URL http://0.0.0.0:8888/api/
