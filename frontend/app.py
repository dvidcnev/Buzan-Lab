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
            nav_options.append("Dropdown Settings")
        if role == "admin":
            nav_options.append("Audit Log")
        action = st.radio("Select Action:", nav_options)
    
    # Set up headers for authenticated requests
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    if action == "View & Search":
        st.subheader("Search and Filter Storage Records")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            search_type = st.selectbox("Search by:", ["All Records", "Specimen ID", "Tube ID"])
        
        search_term = None
        if search_type == "Specimen ID":
            search_term = st.text_input("Enter Specimen ID (LME####):", placeholder="LME0001")
        elif search_type == "Tube ID":
            search_term = st.text_input("Enter Tube ID (LME####-##):", placeholder="LME0001-01")
        
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
                if search_type == "Specimen ID" and search_term:
                    if not re.match(r'^LME\d{4}$', search_term):
                        st.error("Specimen ID must be in format LME#### (e.g., LME0001)")
                    else:
                        resp = requests.get(f"{BACKEND_URL}/storage/specimen/{search_term}", headers=headers)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data:
                                df = pd.DataFrame(data)
                                st.success(f"Found {len(data)} record(s)")
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info(f"No records found with Specimen ID '{search_term}'")
                        else:
                            st.warning("Error retrieving records")
                
                elif search_type == "Tube ID" and search_term:
                    if not re.match(r'^LME\d{4}-\d{2}$', search_term):
                        st.error("Tube ID must be in format LME####-## (e.g., LME0001-01)")
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
                            
                            # Add export buttons before displaying data
                            export_col1, export_col2 = st.columns(2)
                            with export_col1:
                                if st.button("📥 Download All Records to Excel", key="export_all"):
                                    try:
                                        export_resp = requests.post(
                                            f"{BACKEND_URL}/storage/export",
                                            headers=headers,
                                            json=None
                                        )
                                        if export_resp.status_code == 200:
                                            st.download_button(
                                                label="💾 Click to Download Excel File",
                                                data=export_resp.content,
                                                file_name=f"buzan_lab_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                            )
                                        else:
                                            st.error("Failed to export data")
                                    except Exception as e:
                                        st.error(f"Export error: {str(e)}")
                            
                            st.write("---")
                            
                            # Filter columns to display
                            st.subheader("Filter Columns")
                            columns = st.multiselect(
                                "Select columns to display:",
                                options=df.columns.tolist(),
                                default=["id", "specimen_id", "tube_id", "storage_freezer_fridge", "storage_draw", "user_name_and_surname"]
                            )
                            
                            if columns:
                                # Add checkbox column for selective export
                                st.subheader("Select Records for Export")
                                
                                # Add select all checkbox
                                select_all = st.checkbox("Select All Records", key="select_all")
                                
                                # Create selection state
                                if "selected_records" not in st.session_state:
                                    st.session_state.selected_records = []
                                
                                if select_all:
                                    st.session_state.selected_records = [row["specimen_id"] for row in data]
                                
                                # Display data with checkboxes
                                selected_ids = []
                                for idx, row in enumerate(data):
                                    checkbox_col, *data_cols = st.columns([1] + [3] * len(columns))
                                    
                                    with checkbox_col:
                                        is_selected = st.checkbox(
                                            "",
                                            value=row["specimen_id"] in st.session_state.selected_records,
                                            key=f"check_{row['specimen_id']}_{idx}"
                                        )
                                        if is_selected:
                                            selected_ids.append(row["specimen_id"])
                                    
                                    for col_idx, col in enumerate(columns):
                                        with data_cols[col_idx]:
                                            if idx == 0:
                                                st.write(f"**{col}**")
                                            st.write(str(row.get(col, "")))
                                    
                                    if idx < len(data) - 1:
                                        st.divider()
                                
                                # Export selected button
                                if selected_ids:
                                    st.write(f"**{len(selected_ids)} record(s) selected**")
                                    if st.button(f"📥 Download Selected {len(selected_ids)} Record(s) to Excel", key="export_selected"):
                                        try:
                                            export_resp = requests.post(
                                                f"{BACKEND_URL}/storage/export",
                                                headers=headers,
                                                json=selected_ids
                                            )
                                            if export_resp.status_code == 200:
                                                st.download_button(
                                                    label="💾 Click to Download Selected Records",
                                                    data=export_resp.content,
                                                    file_name=f"buzan_lab_selected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                    key="download_selected"
                                                )
                                            else:
                                                st.error("Failed to export selected data")
                                        except Exception as e:
                                            st.error(f"Export error: {str(e)}")
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
        
        detail_tube_id = st.text_input("Enter Tube ID (LME####-##) to view/edit details:", placeholder="LME0001-01", key="detail_tube")
        
        if detail_tube_id and st.button("Load Details"):
            try:
                if not re.match(r'^LME\d{4}-\d{2}$', detail_tube_id):
                    st.error("Tube ID must be in format LME####-## (e.g., LME0001-01)")
                else:
                    resp = requests.get(f"{BACKEND_URL}/storage/tube/{detail_tube_id}", headers=headers)
                    if resp.status_code == 200:
                        record = resp.json()
                        st.json(record)
                        
                        # Show delete button only for admin
                        if st.session_state.user["role"] == "admin":
                            st.write("---")
                            st.subheader("🗑️ Delete Record")
                            delete_password = st.text_input("Enter your password to confirm deletion:", type="password", key=f"del_pass_{detail_tube_id}")
                            if st.button(f"Delete Record {detail_tube_id}", key=f"delete_{detail_tube_id}"):
                                if not delete_password:
                                    st.error("Password is required for deletion")
                                else:
                                    del_resp = requests.delete(
                                        f"{BACKEND_URL}/storage/{detail_tube_id}", 
                                        headers=headers,
                                        json={"password": delete_password}
                                    )
                                    if del_resp.status_code == 200:
                                        st.success("✅ Record deleted successfully!")
                                    elif del_resp.status_code == 401:
                                        st.error("❌ Invalid password")
                                    else:
                                        st.error("Failed to delete record")
                        
                        # Show edit form for admin and editor
                        if st.session_state.user["role"] in ["admin", "editor"]:
                            st.write("---")
                            st.subheader("✏️ Edit Record")
                            with st.form(key=f"edit_form_{detail_tube_id}"):
                                edit_col1, edit_col2 = st.columns(2)
                                with edit_col1:
                                    edit_specimen_id = st.text_input("Specimen ID (LME Number - LME####)", value=record.get("specimen_id", ""))
                                    edit_tube_id = st.text_input("Tube ID (LME + Tissue Number - LME####-##)", value=record.get("tube_id", ""))
                                    edit_tissue_type = st.text_input("Tissue Type", value=record.get("tissue_type", "") or "")
                                    edit_tissue_subtype = st.text_input("Tissue Subtype", value=record.get("tissue_subtype", "") or "")
                                    edit_storage_batch = st.text_input("Storage ID - Extraction Batch", value=record.get("storage_id_extraction_batch", "") or "")
                                    edit_freezer_fridge = st.text_input("Freezer/Fridge Location", value=record.get("storage_freezer_fridge", "") or "")
                                    edit_storage_draw = st.text_input("Storage Drawer", value=record.get("storage_draw", "") or "")
                                
                                with edit_col2:
                                    edit_extraction_link = st.text_input("Extraction Data Link", value=record.get("extraction_data_link", "") or "")
                                    edit_pcr_link = st.text_input("PCR and Gel Data Link", value=record.get("pcr_and_gel_data_link", "") or "")
                                    edit_post_pcr_link = st.text_input("Post-PCR Data Link", value=record.get("post_pcr_data_link", "") or "")
                                    edit_user_name = st.text_input("User Name and Surname", value=record.get("user_name_and_surname", "") or "")
                                
                                edit_notes = st.text_area("Notes about Sample", value=record.get("notes_about_sample", "") or "", height=100)
                                edit_extra_note = st.text_area("Extra Notes", value=record.get("extra_note", "") or "", height=100)
                                edit_password = st.text_input("Enter your password to confirm changes:", type="password")
                                
                                edit_submit = st.form_submit_button("💾 Save Changes")
                                
                                if edit_submit:
                                    if not edit_password:
                                        st.error("Password is required for editing")
                                    elif not edit_specimen_id.strip():
                                        st.error("Specimen ID is required")
                                    elif not re.match(r'^LME\d{4}$', edit_specimen_id):
                                        st.error("Specimen ID must be in format LME#### (e.g., LME0001)")
                                    elif not edit_tube_id.strip():
                                        st.error("Tube ID is required")
                                    elif not re.match(r'^LME\d{4}-\d{2}$', edit_tube_id):
                                        st.error("Tube ID must be in format LME####-## (e.g., LME0001-01)")
                                    else:
                                        edit_payload = {
                                            "specimen_id": edit_specimen_id,
                                            "tube_id": edit_tube_id,
                                            "tissue_type": edit_tissue_type if edit_tissue_type.strip() else None,
                                            "tissue_subtype": edit_tissue_subtype if edit_tissue_subtype.strip() else None,
                                            "storage_id_extraction_batch": edit_storage_batch if edit_storage_batch.strip() else None,
                                            "storage_freezer_fridge": edit_freezer_fridge if edit_freezer_fridge.strip() else None,
                                            "storage_draw": edit_storage_draw if edit_storage_draw.strip() else None,
                                            "extraction_data_link": edit_extraction_link if edit_extraction_link.strip() else None,
                                            "pcr_and_gel_data_link": edit_pcr_link if edit_pcr_link.strip() else None,
                                            "post_pcr_data_link": edit_post_pcr_link if edit_post_pcr_link.strip() else None,
                                            "user_name_and_surname": edit_user_name if edit_user_name.strip() else None,
                                            "notes_about_sample": edit_notes if edit_notes.strip() else None,
                                            "extra_note": edit_extra_note if edit_extra_note.strip() else None,
                                            "password": edit_password
                                        }
                                        edit_resp = requests.put(
                                            f"{BACKEND_URL}/storage/{detail_tube_id}",
                                            json=edit_payload,
                                            headers=headers
                                        )
                                        if edit_resp.status_code == 200:
                                            st.success("✅ Record updated successfully!")
                                            st.json(edit_resp.json())
                                        elif edit_resp.status_code == 401:
                                            st.error("❌ Invalid password")
                                        else:
                                            error_detail = edit_resp.json().get("detail", "Unknown error")
                                            st.error(f"❌ Failed to update record: {error_detail}")
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
            
            # Fetch next available IDs
            try:
                lme_resp = requests.get(f"{BACKEND_URL}/storage/next-lme", headers=headers)
                if lme_resp.status_code == 200:
                    next_lme = lme_resp.json().get("next_lme", "LME0001")
                else:
                    next_lme = "LME0001"
            except:
                next_lme = "LME0001"
            
            st.info(f"ℹ️ **Next Available Specimen ID (LME Number):** `{next_lme}` - This will be auto-generated")
            st.info(f"ℹ️ **Tube ID will be auto-generated** based on the Specimen ID (e.g., {next_lme}-01)")
            
            # Fetch tissue type options
            try:
                tissue_resp = requests.get(f"{BACKEND_URL}/dropdowns?category=tissue_type", headers=headers)
                if tissue_resp.status_code == 200:
                    tissue_options = [t["value"] for t in tissue_resp.json()]
                else:
                    tissue_options = []
            except:
                tissue_options = []
            
            col1, col2 = st.columns(2)
            with col1:
                use_auto_ids = st.checkbox("Use Auto-Generated IDs (Recommended)", value=True)
                # Tissue type selection
                if tissue_options:
                    tissue_type = st.selectbox("Tissue Type", options=[""] + tissue_options)
                else:
                    tissue_type = st.text_input("Tissue Type", placeholder="Optional - e.g., Blood, Tissue, Plasma")
                
                tissue_subtype = st.text_input("Tissue Subtype/Classification", placeholder="Optional - Additional tissue details")
                
                
                if use_auto_ids:
                    specimen_id_val = ""  # Will be auto-generated
                    tube_id_val = ""  # Will be auto-generated
                    st.text_input("Specimen ID (Auto-Generated)", value=next_lme, disabled=True)
                    st.text_input("Tube ID (Auto-Generated)", value=f"{next_lme}-01", disabled=True)
                else:
                    specimen_id_val = st.text_input("Specimen ID (LME Number - LME####)", placeholder="LME0001")
                    tube_id_val = st.text_input("Tube ID (LME + Tissue Number - LME####-##)", placeholder="LME0001-01")
                
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
                    # Validate only if not using auto-generated IDs
                    if not use_auto_ids:
                        if not specimen_id_val.strip():
                            st.error("Specimen ID is required")
                            st.stop()
                        elif not re.match(r'^LME\d{4}$', specimen_id_val):
                            st.error("Specimen ID must be in format LME#### (e.g., LME0001)")
                            st.stop()
                        elif not tube_id_val.strip():
                            st.error("Tube ID is required")
                            st.stop()
                        elif not re.match(r'^LME\d{4}-\d{2}$', tube_id_val):
                            st.error("Tube ID must be in format LME####-## (e.g., LME0001-01)")
                            st.stop()
                    
                    payload = {
                        "specimen_id": specimen_id_val if not use_auto_ids and specimen_id_val.strip() else None,
                        "tube_id": tube_id_val if not use_auto_ids and tube_id_val.strip() else None,
                        "tissue_type": tissue_type if tissue_type and tissue_type.strip() else None,
                        "tissue_subtype": tissue_subtype if tissue_subtype.strip() else None,
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
                        result = resp.json()
                        st.success(f"✅ Storage record added successfully!")
                        st.success(f"📋 Specimen ID: **{result['specimen_id']}**")
                        st.success(f"🧪 Tube ID: **{result['tube_id']}**")
                        st.json(result)
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
            specimen_filter = st.text_input("Specimen ID contains", key="audit_specimen")
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
            if specimen_filter:
                params["specimen_id"] = specimen_filter
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
