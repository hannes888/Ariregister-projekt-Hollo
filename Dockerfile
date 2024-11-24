FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

COPY wait-for-it.sh /wait-for-it.sh

CMD ["sh", "-c", "/wait-for-it.sh flask_db:5432 -- flask run --host=0.0.0.0"]