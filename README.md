# DataFlow — CSV/Excel Search Tool

A production-ready data search tool. Upload any CSV or Excel file and search through it instantly.

---

## Setup (One Time)

### 1. Install Python dependencies

```bash
cd dataflow
pip install -r requirements.txt
```

### 2. Run the backend

```bash
python main.py
```

Server starts at: http://localhost:8000

### 3. Open the frontend

Open `frontend/index.html` in your browser.

> **Tip:** For a better experience, serve the frontend with a simple HTTP server:
> ```bash
> cd frontend
> python -m http.server 3000
> ```
> Then open http://localhost:3000

---

## Project Structure

```
dataflow/
├── main.py              
├── requirements.txt    
├── database.db          
├── frontend/
│   └── index.html       
└── utils/
    ├── upload.py        
    └── search.py        
```

---

## Features

| Feature | Description |
|---|---|
| Upload CSV/Excel | Drag & drop or click to upload |
| Full-text search | Search across ALL columns at once |
| Column filter | Search within a specific column |
| Sort | Click any column header to sort |
| Pagination | 20/50/100/200 rows per page |
| Download | Export search results as CSV |
| Highlight | Matching text highlighted in results |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/upload` | Upload file |
| GET | `/api/data` | Get paginated data |
| GET | `/api/search?q=...` | Search data |
| GET | `/api/columns` | Get column names |
| GET | `/api/download` | Download filtered CSV |

---

## For Usage


1. Upload the Excel/CSV file
2. Type anything in the search box
3. Hit Download to save results
