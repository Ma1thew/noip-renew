FROM python:3.6-onbuild
ADD . /usr/src/app
CMD ["python", "./main.py"]
