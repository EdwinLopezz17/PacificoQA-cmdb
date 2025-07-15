import streamlit as st
import requests

API_URL = "http://localhost:3001/api"

def login():
    st.title("🔐 QA Inventory Analyzer - Login")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                json={"username": username, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                token = response.json()["token"]
                st.session_state["token"] = token
                st.experimental_rerun()
            else:
                st.error("Credenciales inválidas.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")
