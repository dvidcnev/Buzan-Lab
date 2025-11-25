from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example in-memory data
data = pd.DataFrame({
    'id': [1, 2, 3],
    'value': [10, 20, 30]
})

@app.get("/data")
def get_data():
    return data.to_dict(orient="records")

@app.post("/add")
def add_data(item: dict):
    global data
    data = pd.concat([data, pd.DataFrame([item])], ignore_index=True)
    return {"status": "success", "data": data.to_dict(orient="records")}
