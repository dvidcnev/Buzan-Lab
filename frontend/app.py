import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "http://localhost:8000"

st.title("Data Dashboard")

# Fetch data from backend
if st.button("Load Data"):
    resp = requests.get(f"{BACKEND_URL}/data")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        st.dataframe(df)
    else:
        st.error("Failed to load data")

# Add new data
st.subheader("Add Data")
new_id = st.number_input("ID", min_value=1, step=1)
new_value = st.number_input("Value", step=1)
if st.button("Add Row"):
    resp = requests.post(f"{BACKEND_URL}/add", json={"id": new_id, "value": new_value})
    if resp.status_code == 200:
        st.success("Row added!")
    else:
        st.error("Failed to add row")
