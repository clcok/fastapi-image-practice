import sqlite3
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from .database import get_db, init_db
from .schemas import ImageRead, ImageUpdate

UPLOAD_DIR = Path("uploads")
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup: create the table and the upload folder.
    init_db()
    UPLOAD_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(title="Image API", lifespan=lifespan)


def to_response(row: sqlite3.Row) -> ImageRead:
    return ImageRead(**dict(row), url=f"/images/{row['id']}/file")


def get_row_or_404(image_id: int, db: sqlite3.Connection) -> sqlite3.Row:
    row = db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return row


@app.get("/")
def root():
    return {"message": "Image API is running. See /docs"}


@app.post("/images", response_model=ImageRead, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=200),
    description: str | None = Form(None, max_length=1000),
    db: sqlite3.Connection = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported type {file.content_type}. Allowed: {list(ALLOWED_TYPES)}",
        )

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")

    # Random stored name avoids collisions and path tricks in user filenames.
    stored_name = f"{uuid.uuid4().hex}{ALLOWED_TYPES[file.content_type]}"
    (UPLOAD_DIR / stored_name).write_bytes(data)

    # Always use ? placeholders, never f-strings, to prevent SQL injection.
    cur = db.execute(
        """
        INSERT INTO images (title, description, original_filename, stored_filename, content_type, size_bytes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, description, file.filename or "unknown", stored_name, file.content_type, len(data)),
    )
    db.commit()
    return to_response(get_row_or_404(cur.lastrowid, db))


@app.get("/images", response_model=list[ImageRead])
def list_images(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_db),
):
    rows = db.execute(
        "SELECT * FROM images ORDER BY id LIMIT ? OFFSET ?", (limit, skip)
    ).fetchall()
    return [to_response(r) for r in rows]


@app.get("/images/{image_id}", response_model=ImageRead)
def get_image(image_id: int, db: sqlite3.Connection = Depends(get_db)):
    return to_response(get_row_or_404(image_id, db))


@app.get("/images/{image_id}/file")
def download_image(image_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = get_row_or_404(image_id, db)
    path = UPLOAD_DIR / row["stored_filename"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file missing on disk")
    return FileResponse(path, media_type=row["content_type"], filename=row["original_filename"])


@app.patch("/images/{image_id}", response_model=ImageRead)
def update_image(image_id: int, payload: ImageUpdate, db: sqlite3.Connection = Depends(get_db)):
    get_row_or_404(image_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if changes:
        # Column names come from our own Pydantic model, not the user, so this is safe.
        set_clause = ", ".join(f"{col} = ?" for col in changes)
        db.execute(f"UPDATE images SET {set_clause} WHERE id = ?", (*changes.values(), image_id))
        db.commit()
    return to_response(get_row_or_404(image_id, db))


@app.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = get_row_or_404(image_id, db)
    (UPLOAD_DIR / row["stored_filename"]).unlink(missing_ok=True)
    db.execute("DELETE FROM images WHERE id = ?", (image_id,))
    db.commit()
