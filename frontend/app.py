import streamlit as st
import requests
import pandas as pd
import re

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Buzan Lab Storage Management", layout="wide")
st.title("Buzan Lab Storage Management")

# Initialize session state for form
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")
    action = st.radio("Select Action:", ["View & Search", "Add New Record"])

if action == "View & Search":
    st.subheader("Search and Filter Storage Records")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        search_type = st.selectbox("Search by:", ["All Records", "Tube ID", "Specimen ID"])
    
    search_term = None
    if search_type == "Tube ID":
        search_term = st.text_input("Enter Tube/Well ID (LME####):", placeholder="LME0001")
    elif search_type == "Specimen ID":
        search_term = st.text_input("Enter Specimen ID (LME####-##):", placeholder="LME0001-01")
    
    with col2:
        skip = st.number_input("Skip", min_value=0, step=10, value=0)
    with col3:
        limit = st.number_input("Limit", min_value=1, max_value=1000, value=50)
    
    # Search button
    if st.button("🔍 Search", key="search_btn"):
        try:
            if search_type == "Tube ID" and search_term:
                if not re.match(r'^LME\d{4}$', search_term):
                    st.error("Tube ID must be in format LME#### (e.g., LME0001)")
                else:
                    resp = requests.get(f"{BACKEND_URL}/storage/tube/{search_term}")
                    if resp.status_code == 200:
                        data = [resp.json()]
                        df = pd.DataFrame(data)
                        st.success(f"Found 1 record")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning(f"No record found with Tube ID '{search_term}'")
            
            elif search_type == "Specimen ID" and search_term:
                if not re.match(r'^LME\d{4}-\d{2}$', search_term):
                    st.error("Specimen ID must be in format LME####-## (e.g., LME0001-01)")
                else:
                    resp = requests.get(f"{BACKEND_URL}/storage/specimen/{search_term}")
                    if resp.status_code == 200:
                        data = resp.json()
                        if data:
                            df = pd.DataFrame(data)
                            st.success(f"Found {len(data)} records")
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info(f"No records found with Specimen ID '{search_term}'")
                    else:
                        st.warning("Error retrieving records")
            
            elif search_type == "All Records":
                resp = requests.get(f"{BACKEND_URL}/storage", params={"skip": skip, "limit": limit})
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        df = pd.DataFrame(data)
                        st.success(f"Loaded {len(data)} records")
                        
                        # Filter columns to display
                        st.subheader("Filter Columns")
                        columns = st.multiselect(
                            "Select columns to display:",
                            options=df.columns.tolist(),
                            default=["tube_or_well_id", "specimen_id", "storage_freezer_fridge", "storage_draw", "user_name_and_surname"]
                        )
                        
                        if columns:
                            st.dataframe(df[columns], use_container_width=True)
                        else:
                            st.warning("Please select at least one column")
                    else:
                        st.info("No records found")
                else:
                    st.error("Error retrieving records")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Display record details if needed
    st.divider()
    st.subheader("Record Details & Actions")
    
    detail_tube_id = st.text_input("Enter Tube ID to view/edit details:", placeholder="LME0001", key="detail_tube")
    
    if detail_tube_id and st.button("Load Details"):
        try:
            if not re.match(r'^LME\d{4}$', detail_tube_id):
                st.error("Tube ID must be in format LME#### (e.g., LME0001)")
            else:
                resp = requests.get(f"{BACKEND_URL}/storage/tube/{detail_tube_id}")
                if resp.status_code == 200:
                    record = resp.json()
                    st.json(record)
                    
                    col_delete = st.columns(1)[0]
                    with col_delete:
                        if st.button(f"🗑️ Delete Record {detail_tube_id}", key=f"delete_{detail_tube_id}"):
                            del_resp = requests.delete(f"{BACKEND_URL}/storage/{detail_tube_id}")
                            if del_resp.status_code == 200:
                                st.success("Record deleted successfully!")
                            else:
                                st.error("Failed to delete record")
                else:
                    st.warning("Record not found")
        except Exception as e:
            st.error(f"Error: {str(e)}")

else:  # Add New Record
    st.subheader("Add New Storage Record")
    
    col1, col2 = st.columns(2)
    with col1:
        tube_id = st.text_input("Tube/Well ID (LME####)", placeholder="LME0001")
        specimen_id = st.text_input("Specimen ID (LME####-##)", placeholder="LME0001-01")
        storage_batch = st.text_input("Storage ID - Extraction Batch", placeholder="Optional")
        freezer_fridge = st.text_input("Freezer/Fridge Location", placeholder="Optional")
        storage_draw = st.text_input("Storage Drawer", placeholder="Optional")
    
    with col2:
        extraction_link = st.text_input("Extraction Data Link", placeholder="Optional")
        pcr_link = st.text_input("PCR and Gel Data Link", placeholder="Optional")
        post_pcr_link = st.text_input("Post-PCR Data Link", placeholder="Optional")
        user_name = st.text_input("User Name and Surname", placeholder="Optional")
    
    notes = st.text_area("Notes about Sample", placeholder="Optional", height=100)
    extra_note = st.text_area("Extra Notes", placeholder="Optional", height=100)
    
    if st.button("➕ Add Record", key="add_record"):
        try:
            # Validate required fields
            if not tube_id.strip():
                st.error("Tube/Well ID is required")
            elif not re.match(r'^LME\d{4}$', tube_id):
                st.error("Tube/Well ID must be in format LME#### (e.g., LME0001)")
            elif not specimen_id.strip():
                st.error("Specimen ID is required")
            elif not re.match(r'^LME\d{4}-\d{2}$', specimen_id):
                st.error("Specimen ID must be in format LME####-## (e.g., LME0001-01)")
            else:
                payload = {
                    "tube_or_well_id": tube_id,
                    "specimen_id": specimen_id,
                    "storage_id_extraction_batch": storage_batch if storage_batch.strip() else None,
                    "storage_freezer_fridge": freezer_fridge if freezer_fridge.strip() else None,
                    "storage_draw": storage_draw if storage_draw.strip() else None,
                    "extraction_data_link": extraction_link if extraction_link.strip() else None,
                    "pcr_and_gel_data_link": pcr_link if pcr_link.strip() else None,
                    "post_pcr_data_link": post_pcr_link if post_pcr_link.strip() else None,
                    "user_name_and_surname": user_name if user_name.strip() else None,
                    "notes_about_sample": notes if notes.strip() else None,
                    "extra_note": extra_note if extra_note.strip() else None
                }
                resp = requests.post(f"{BACKEND_URL}/storage", json=payload)
                if resp.status_code == 200:
                    st.success(f"✅ Storage record {tube_id} added successfully!")
                    st.json(resp.json())
                else:
                    error_detail = resp.json().get("detail", "Unknown error")
                    st.error(f"❌ Failed to add record: {error_detail}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.caption("Buzan Lab Storage Management - Connected to Backend API")
