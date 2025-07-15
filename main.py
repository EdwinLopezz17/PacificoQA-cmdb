import streamlit as st
from app import auth, analysis, exceptions

st.set_page_config(page_title="QA Inventory Analyzer", layout="wide")

# Si no está logueado, mostrar login
if "token" not in st.session_state:
    auth.login()
else:
    st.sidebar.button("Cerrar sesión", on_click=lambda: st.session_state.pop("token"))
    analysis.run_analysis()
    exceptions.manage_exceptions()
