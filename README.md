# Task Manager

## Установка и запуск

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/tatitrif/task_manager.git
   cd task_manager
   ```

## Структура проекта

```
task_manager/
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
