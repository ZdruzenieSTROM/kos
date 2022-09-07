FROM python:3.8.2

WORKDIR /app
COPY . /app/



RUN pip install -r requirements.txt
RUN pip install daphne
RUN python manage.py migrate

EXPOSE 8000

CMD daphne -b 0.0.0.0 -p 8000 online_competitions.asgi:application