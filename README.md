# online-sutaze

Projekt slúži na organizovanie online súťaží združenia STROM ako napríklad **Máš problém?!** a **Kôš**. Je možné ho použiť aj na sústredeniach alebo iných aktivitách, kde sa dá využiť tento herný systém.

## Inštalácia
Aplikácia beží na Pythone 3.8. Nainštaluj requirements:
```
pip install -r requirements.txt
```

## Inicializácia
```
python manage.py migrate
python manage.py loaddata test_game test_team
```

## Spustenie
```
python manage.py runserver
```