import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn
from utils.upload import process_upload
from utils.search import fetch_data, search_data, get_columns, download_csv

app = FastAPI(title="DataFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve index.html without needing aiofiles
@app.get("/")
def root():
    html_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in [".csv", ".xlsx", ".xls"]):
        raise HTTPException(400, "Only CSV and Excel files are supported.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(400, "File is empty.")

    try:
        result = process_upload(contents, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return result


@app.get("/api/data")
def get_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_col: str = Query(None),
    sort_dir: str = Query("asc")
):
    return fetch_data(page, page_size, sort_col, sort_dir)


@app.get("/api/search")
def search(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    col_filter: str = Query(None)
):
    return search_data(q, page, page_size, col_filter)


@app.get("/api/columns")
def columns():
    return get_columns()


@app.get("/api/download")
def download(q: str = Query(None), col_filter: str = Query(None)):
    csv_content = download_csv(q, col_filter)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"}
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
