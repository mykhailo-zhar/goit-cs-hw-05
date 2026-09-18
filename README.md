# goit-cs-hw-05

Домашня робота з курсу **Computer Systems** (GoIT): асинхронне сортування файлів за розширенням і підрахунок частоти слів у тексті за парадигмою MapReduce.

## Завдання 1. Асинхронне копіювання файлів

Скрипт рекурсивно читає файли у вихідній папці та копіює їх у директорію призначення, розкладаючи по підпапках за розширенням (наприклад `.txt`, `.js`). Файли без розширення потрапляють у `other`. Читання і копіювання виконуються асинхронно (`asyncio`, `aiopath`, `aioshutil`). Помилки пишуться в stdout і в `logs/`.

Якщо кілька файлів мають однакове ім’я, наступні копії отримують суфікс із відносним шляхом джерела.

```bash
python src/copy_script.py -s /path/to/source -d /path/to/destination
```

| Аргумент | Опис |
| --- | --- |
| `-s`, `--source` | Вихідна папка (обов’язковий) |
| `-d`, `--destination` | Папка призначення (за замовчуванням `./dist`) |
| `-l`, `--limit` | Глибина обходу підпапок (`-1` — без обмеження) |

Основна логіка: [`src/file_copy.py`](src/file_copy.py). CLI: [`src/copy_script.py`](src/copy_script.py).

## Завдання 2. MapReduce і візуалізація топ-слів

Скрипт завантажує текст з URL, рахує частоту слів через MapReduce у пулі процесів і показує горизонтальну діаграму топ-слів (`matplotlib`).

```bash
python src/map_reduce.py
```

За замовчуванням береться текст з [Project Gutenberg](https://gutenberg.net.au/ebooks01/0100021.txt). Слова нормалізуються до нижнього регістру, пунктуація відкидається. Код: [`src/map_reduce.py`](src/map_reduce.py).

## Передумови

- [mise](https://mise.jdx.dev/getting-started.html) встановлений і активований у шелі (наприклад `eval "$(mise activate bash)"` для Bash).

Python зафіксовано в [mise.toml](mise.toml) (типово **3.12**, можна перевизначити через `PYTHON_VERSION`). Репозиторій також містить [`.python-version`](.python-version).

## Швидкий старт

1. **Довірити проєкт і встановити інструменти** (з кореня репозиторію):
   ```bash
   mise trust
   mise install
   ```
   Це ставить **Python**, **uv** і **ruff**; `python.uv_venv_auto` керує [`.venv`](.venv).
2. **Встановити залежності** ([pyproject.toml](pyproject.toml) + [uv.lock](uv.lock)):
   ```bash
   uv sync
   ```
3. **Поставити pre-commit хуки** (один раз після `uv sync`):
   ```bash
   mise run pre-commit-install
   ```

## Структура

- [`src/copy_script.py`](src/copy_script.py), [`src/file_copy.py`](src/file_copy.py) — завдання 1
- [`src/map_reduce.py`](src/map_reduce.py) — завдання 2
- [`src/utility.py`](src/utility.py) — спільне логування
- [`tests/`](tests/) — тести (pytest)
- [`docs/`](docs/) — документація Sphinx
- [`logs/`](logs/) — файли логів копіювання

## Команди

| Мета | Команда |
| --- | --- |
| Запустити тести | `mise run test` або `uv run pytest tests/` |
| Лінт | `mise run lint` |
| Інформація про проєкт / venv | `mise run info` |
| Оновити Sphinx API stubs | `mise run generate-docs` (`mise run gd`) |
| Зібрати HTML-документацію | `mise run build-docs` (`mise run bd`) |
| Встановити pre-commit хуки | `mise run pre-commit-install` |

HTML після збірки лежить у `docs/build/` (`docs/build/index.html`).

## Ліцензія

Див. [LICENSE](LICENSE).
