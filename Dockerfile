FROM python:3.8.2

ARG SETTINGS_MODULE=online_competitions.settings.prod_settings

EXPOSE 8000

WORKDIR /app

COPY requirements.txt /app/

RUN ["pip", "install", "-r", "requirements.txt"]
RUN ["pip", "install", "daphne"]

COPY . /app/

RUN chmod +x /app/entrypoint.sh
ENV DJANGO_SETTINGS_MODULE=$SETTINGS_MODULE

CMD ["/app/entrypoint.sh"]

