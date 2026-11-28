# online-sutaze

Projekt slúži na organizovanie online súťaží združenia STROM ako napríklad **Máš problém?!** a **Kôš**. Je možné ho použiť aj na sústredeniach alebo iných aktivitách, kde sa dá využiť tento herný systém.

## Inštalácia
Aplikácia beží na Pythone 3.15. Nainštaluj requirements:
```
pip install -r requirements.txt
```

## Inicializácia
```
python manage.py migrate
python manage.py loaddata base test_game test_team
```

## Spustenie
```
python manage.py runserver
```

## Runtime and dependency updates

Use CPython 3.15 (tested with 3.15.2) and Django 6.1.3. These are the current
stable [Python](https://www.python.org/downloads/source/) and
[Django](https://www.djangoproject.com/download/) releases as of 2026-11-28.
The supported Python series is recorded in `.python-version`.

Create a fresh environment when switching Python versions:

```sh
python3.15 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

Direct dependencies live in `requirements.in`; `requirements.txt` pins their
complete dependency graph. Refresh the generated file with
[uv](https://docs.astral.sh/uv/):

```sh
uv pip compile --universal --python-version 3.15 requirements.in -o requirements.txt
```

Development tools are kept out of deployment installs. Install them with
`python -m pip install -r requirements-dev.txt`. After updating runtime pins,
refresh the development lock as well:

```sh
uv pip compile --universal --python-version 3.15 requirements-dev.in -o requirements-dev.txt
```

The unused `nose`/`django-nose` dependencies were removed; tests use Django's
standard test runner.

Run isolated checks with `DJANGO_SETTINGS_MODULE=online_competitions.settings_ci`
(and the dummy secret environment variables shown in `.github/workflows/ci.yaml`
where required). This selects an in-memory SQLite database and in-memory email,
and collects static files under the system temporary directory:

```sh
export DJANGO_SETTINGS_MODULE=online_competitions.settings_ci
python manage.py check
python manage.py migrate --noinput
python manage.py test --noinput
python manage.py collectstatic --noinput
```

The CI workflow installs the pinned dependencies and runs these checks on Python
3.15. Local validation covered clean per-project environments, migrations, tests,
and static collection.

Regression tests replay both historical `0029` migration branch orders, verify
registration email confirmation, and complete a password reset through the
project's custom forms.

The deployment image uses `python:3.15-trixie`. Daphne is pinned in the runtime
lock instead of installed separately without a version. Local validation includes
HTTP startup through Daphne. CI also builds the deployment image on Linux;
Docker is not installed on the local validation host.
