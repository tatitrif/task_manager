# Task Manager

Веб-приложение для управления задачами в команде.

## Описание

Этот проект представляет собой веб-приложение.

## Технологии

- **Backend**: Django

## Установка и запуск

```bash
# клонируйте репозиторий
git clone https://github.com/tatitrif/task_manager.git

# перейдите в директорию приложения
cd task_manager/backend

# запустите миграцию (для создания бд)
python manage.py migrate

# запустите приложение
python manage.py runserver
```

## Структура проекта

```
task_manager/
├── backend/# Django-приложение
│   ├── config/ # Django-проект
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── asgi.py
│   ├── .env
│   └── manage.py
├── .gitignore
├── .pre-commit-config.yaml # конфигурация хуков
├── pyproject.toml # конфигурация проекта
└── README.md # информация о проекте
```

## Pre-commit

Проект использует фреймворк .pre-commit-config.yaml для автоматической проверки кода, например, линтинг, форматирование или запуск тестов, перед отправкой изменений в репозиторий.

```bash

# установить pre-commit на устройство
pip install pre-commit==3.8.0

# установить pre-commit в репозитории
pre-commit install

# выполнение pre-commit без коммита
pre-commit run --all-files

# выполнение коммита без pre-commit
git commit --no-verify -m "<message>"

```
