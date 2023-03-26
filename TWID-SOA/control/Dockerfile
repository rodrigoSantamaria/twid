FROM python:3.10-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8001

ENTRYPOINT ["python3"]

CMD ["-m", "uvicorn", "main:app", "--port", "8001", "--host", "0.0.0.0"]