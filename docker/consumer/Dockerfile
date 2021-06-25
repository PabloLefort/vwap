FROM python:3.8.1

WORKDIR /app

COPY requirements.pip requirements.pip
RUN pip install -r requirements.pip

COPY . .

CMD ["python", "src/consumer.py"]
