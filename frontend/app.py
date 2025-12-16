import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Buzan Lab Storage Management", layout="wide", initial_sidebar_state="expanded")

# Session state initialization
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

# Login page
if not st.session_state.token:
    st.title("🔐 Buzan Lab - Storage Management Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("---")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/login",
                    json={"username": username, "password": password}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.write("---")
        st.info("**Demo Credentials:**")
        st.write("- **Admin**: admin / admin123")
        st.write("- **Editor**: editor / editor123")
        st.write("- **Viewer**: viewer / viewer123")

else:
    # Main app
    st.title("Buzan Lab Storage Management")
    
    # Sidebar with user info and logout
    with st.sidebar:
        st.write(f"👤 **User:** {st.session_state.user['username']}")
        st.write(f"🔖 **Role:** {st.session_state.user['role'].upper()}")
        
        if st.button("Logout", key="logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
        
        st.write("---")
        
        # Navigation based on role
        role = st.session_state.user["role"]
        nav_options = ["View & Search"]
        if role in ["admin", "editor"]:
            nav_options.append("Add New Record")
        if role == "admin":
            nav_options.append("Audit Log")
        action = st.radio("Select Action:", nav_options)
    
    # Set up headers for authenticated requests
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
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

        with st.expander("Advanced filters"):
            adv_col1, adv_col2, adv_col3 = st.columns(3)
            with adv_col1:
                filter_freezer = st.text_input("Freezer/Fridge contains")
                filter_batch = st.text_input("Extraction batch contains")
                filter_draw = st.text_input("Drawer contains")
            with adv_col2:
                filter_user = st.text_input("User contains")
                filter_notes = st.text_input("Notes text search")
            with adv_col3:
                use_date_filter = st.checkbox("Filter by date range")
                date_from = st.date_input("Date from", value=None, disabled=not use_date_filter)
                date_to = st.date_input("Date to", value=None, disabled=not use_date_filter)
        
        # Search button
        if st.button("🔍 Search", key="search_btn"):
            try:
                if search_type == "Tube ID" and search_term:
                    if not re.match(r'^LME\d{4}$', search_term):
                        st.error("Tube ID must be in format LME#### (e.g., LME0001)")
                    else:
                        resp = requests.get(f"{BACKEND_URL}/storage/tube/{search_term}", headers=headers)
                        if resp.status_code == 200:
                            data = [resp.json()]
                            df = pd.DataFrame(data)
                            st.success(f"Found 1 record")
                            st.dataframe(df, use_container_width=True)
                        elif resp.status_code == 404:
                            st.warning(f"No record found with Tube ID '{search_term}'")
                        else:
                            st.error("Error retrieving record")
                
                elif search_type == "Specimen ID" and search_term:
                    if not re.match(r'^LME\d{4}-\d{2}$', search_term):
                        st.error("Specimen ID must be in format LME####-## (e.g., LME0001-01)")
                    else:
                        resp = requests.get(f"{BACKEND_URL}/storage/specimen/{search_term}", headers=headers)
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
                    params = {"skip": skip, "limit": limit}
                    if filter_freezer:
                        params["storage_freezer_fridge"] = filter_freezer
                    if filter_batch:
                        params["storage_id_extraction_batch"] = filter_batch
                    if filter_draw:
                        params["storage_draw"] = filter_draw
                    if filter_user:
                        params["user_name_and_surname"] = filter_user
                    if filter_notes:
                        params["text"] = filter_notes
                    if use_date_filter and date_from:
                        params["date_from"] = str(date_from)
                    if use_date_filter and date_to:
                        params["date_to"] = str(date_to)

                    resp = requests.get(f"{BACKEND_URL}/storage", params=params, headers=headers)
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
        
        # Display record details & actions
        st.divider()
        st.subheader("Record Details & Actions")
        
        detail_tube_id = st.text_input("Enter Tube ID to view/edit details:", placeholder="LME0001", key="detail_tube")
        
        if detail_tube_id and st.button("Load Details"):
            try:
                if not re.match(r'^LME\d{4}$', detail_tube_id):
                    st.error("Tube ID must be in format LME#### (e.g., LME0001)")
                else:
                    resp = requests.get(f"{BACKEND_URL}/storage/tube/{detail_tube_id}", headers=headers)
                    if resp.status_code == 200:
                        record = resp.json()
                        st.json(record)
                        
                        # Show delete button only for admin
                        if st.session_state.user["role"] == "admin":
                            if st.button(f"🗑️ Delete Record {detail_tube_id}", key=f"delete_{detail_tube_id}"):
                                del_resp = requests.delete(f"{BACKEND_URL}/storage/{detail_tube_id}", headers=headers)
                                if del_resp.status_code == 200:
                                    st.success("Record deleted successfully!")
                                else:
                                    st.error("Failed to delete record")
                    else:
                        st.warning("Record not found")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif action == "Add New Record":
        # Check permission
        role = st.session_state.user["role"]
        if role not in ["admin", "editor"]:
            st.error("❌ You don't have permission to add records. Only ADMIN and EDITOR roles can add records.")
        else:
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
                        resp = requests.post(f"{BACKEND_URL}/storage", json=payload, headers=headers)
                        if resp.status_code == 200:
                            st.success(f"✅ Storage record {tube_id} added successfully!")
                            st.json(resp.json())
                        else:
                            error_detail = resp.json().get("detail", "Unknown error")
                            st.error(f"❌ Failed to add record: {error_detail}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    elif action == "Audit Log":
        st.subheader("Admin Audit Log")
        col1, col2, col3 = st.columns(3)
        with col1:
            action_filter = st.selectbox("Action", ["All", "CREATE", "UPDATE", "DELETE"])
            tube_filter = st.text_input("Tube ID contains", key="audit_tube")
        with col2:
            user_filter = st.text_input("Performed by contains", key="audit_user")
            limit = st.number_input("Limit", min_value=1, max_value=500, value=100, step=10, key="audit_limit")
        with col3:
            audit_use_date_filter = st.checkbox("Filter by date range", key="audit_date_toggle")
            audit_date_from = st.date_input("Date from", value=None, key="audit_from", disabled=not audit_use_date_filter)
            audit_date_to = st.date_input("Date to", value=None, key="audit_to", disabled=not audit_use_date_filter)

        if st.button("Load Audit Log", key="load_audit"):
            params = {"skip": 0, "limit": limit}
            if action_filter != "All":
                params["action"] = action_filter
            if tube_filter:
                params["tube_or_well_id"] = tube_filter
            if user_filter:
                params["performed_by"] = user_filter
            if audit_use_date_filter and audit_date_from:
                params["date_from"] = str(audit_date_from)
            if audit_use_date_filter and audit_date_to:
                params["date_to"] = str(audit_date_to)

            resp = requests.get(f"{BACKEND_URL}/audit/logs", params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    df = pd.DataFrame(data)
                    st.success(f"Loaded {len(data)} audit rows")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No audit entries match the filters")
            else:
                st.error("Failed to load audit log")
    
    # Footer
    st.divider()
    st.caption("Buzan Lab Storage Management - Connected to Backend API")
