FROM python:3.8.2

EXPOSE 8000

WORKDIR /app

COPY requirements.txt /app/

RUN ["pip", "install", "-r", "requirements.txt"]
RUN ["pip", "install", "daphne"]

COPY . /app/

RUN ["python", "manage.py", "migrate"]
RUN ["python", "manage.py", "collectstatic", "--noinput"]

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "online_competitions.asgi:application"]
