# Python Data App: FastAPI + Streamlit

## Manual: Getting Started

### 1. Prerequisites
- Python 3.8+
- All dependencies installed (see `requirements.txt` in each folder)

### 2. Start the Backend (API)
Open a terminal and run:
```powershell
cd backend
uvicorn main:app --reload
```
The API will be available at http://localhost:8000

### 3. Start the Frontend (Dashboard)
Open a new terminal and run:
```powershell
cd frontend
streamlit run app.py
```
The dashboard will open in your browser.

### 4. Stopping the App
Press `Ctrl+C` in each terminal to stop the backend or frontend.

---

## Database Recommendation for Local/Server Use

For storing normalized data samples in a local or server environment:

- **MySQL**: Reliable, widely used, and works well with Python. Good if you already use it.
- **PostgreSQL**: Highly recommended for new projects. Advanced features, strong data integrity, and great for analytics.
- **SQLite**: Simple, file-based, best for prototyping or single-user local apps (not for concurrent/multi-user server scenarios).

**Recommendation:**
If you want robust, production-ready storage, use PostgreSQL. If you are comfortable with MySQL, it is also a solid choice.

You can connect either database to FastAPI using SQLAlchemy for ORM support.

## Features
- View and add data rows via the dashboard.
- Data is managed in-memory for demo purposes.

---

Replace in-memory data logic with your own data source as needed.
