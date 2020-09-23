# OMWebService
OpenModelica web service, queries via a REST API

## Dependencies

- [Python >= 3.8.5](https://www.python.org/)
- [OpenModelica >= 1.16.0](https://openmodelica.org)
- Required python packages are installed via requirement.txt

## Build instructions

Install the dependencies and then run the following commands,

```bash
$ cd /path/to/OpenModelica/OMWebService
$ pip install -r requirements.txt
$ python app.py
```

In your browser, open the URL http://localhost:8888/api/
