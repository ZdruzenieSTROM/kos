FROM python:3.8.2

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt
RUN pip install daphne

COPY . /app/

EXPOSE 8000

CMD daphne -b 0.0.0.0 -p 8000 online_competitions.asgi:application
