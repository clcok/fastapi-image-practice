# fastapi-image-practice

A small FastAPI + SQLite API for uploading and managing images.
Metadata goes in SQLite (`app.db`), and the image files go in `uploads/`.

## Setup (Windows)

Git Bash:

```bash
py -m venv .venv                      # skip if .venv already exists
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

PowerShell:

```powershell
py -m venv .venv                      # skip if .venv already exists
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

With the virtual environment activated (either shell):

```bash
python -m fastapi dev app/main.py
```

Use `python -m fastapi`, not plain `fastapi`: on this PC Windows blocks the
`fastapi.exe` launcher, but running it through Python works.

Then open http://127.0.0.1:8000/docs to try every endpoint in the browser.

## Endpoints

| Method | Path                  | Request                                        | Response              |
|--------|-----------------------|------------------------------------------------|-----------------------|
| POST   | `/images`             | multipart form: `file`, `title`, `description` | 201 + image metadata  |
| GET    | `/images`             | query: `skip`, `limit`                         | list of metadata      |
| GET    | `/images/{id}`        | -                                              | image metadata        |
| GET    | `/images/{id}/file`   | -                                              | the image file        |
| PATCH  | `/images/{id}`        | JSON: `{"title": "...", "description": "..."}` | updated metadata      |
| DELETE | `/images/{id}`        | -                                              | 204 No Content        |

Example with curl:

```bash
curl -F "file=@cat.png" -F "title=My cat" http://127.0.0.1:8000/images
curl http://127.0.0.1:8000/images
```
