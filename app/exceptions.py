import streamlit as st
import requests

API_URL = "http://localhost:3001/api"

def manage_exceptions():
    st.header("⚙️ Gestión de Excepciones")

    token = st.session_state.get("token", "")
    headers = {"Authorization": f"Bearer {token}"}

    # --------------------------
    # FORMULARIO PARA AGREGAR
    # --------------------------
    with st.expander("➕ Agregar nueva excepción", expanded=True):
        with st.form("create_exception_form"):
            col1, col2 = st.columns(2)
            serie = col1.text_input("Número de serie para excepcionar")
            reason = col2.text_input("Motivo de la excepción")

            submitted = st.form_submit_button("Agregar excepción")
            if submitted:
                try:
                    resp = requests.post(
                        f"{API_URL}/exceptions",
                        json={"serie": serie, "reason": reason},
                        headers=headers,
                        timeout=5
                    )
                    if resp.status_code == 201:
                        st.success("✅ Excepción creada correctamente.")
                        st.experimental_rerun()
                    else:
                        st.error("Error al crear excepción.")
                except Exception as e:
                    st.error(f"Error conectando al backend: {e}")

    # --------------------------
    # TABLA DE EXCEPCIONES
    # --------------------------
    st.subheader("📋 Lista de excepciones")

    try:
        resp = requests.get(f"{API_URL}/exceptions", headers=headers, timeout=5)
        if resp.status_code == 200:
            exceptions = resp.json()

            if exceptions:
                # Cabecera
                st.markdown("""
                    <style>

                    </style>
                """, unsafe_allow_html=True)

                # Headers
                col1, col2, col3, col4 = st.columns([2, 3, 3, 2])
                with col1:
                    st.markdown("<div class='table-header'>Serie</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown("<div class='table-header'>Motivo</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown("<div class='table-header'>Editar motivo</div>", unsafe_allow_html=True)
                with col4:
                    st.markdown("<div class='table-header'>Acciones</div>", unsafe_allow_html=True)

                # Filas
                for exc in exceptions:
                    col1, col2, col3, col4 = st.columns([2, 3, 3, 2])

                    with col1:
                        st.markdown(f"<div class='table-row'>{exc['serie']}</div>", unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"<div class='table-row'>{exc['reason']}</div>", unsafe_allow_html=True)

                    with col3:
                        new_reason = st.text_input(
                            label=f"Editar motivo (ID {exc['id']})",
                            value=exc["reason"],
                            key=f"edit_reason_{exc['id']}",
                            label_visibility="collapsed"
                        )
                        if st.button(f"✅ Actualizar {exc['id']}", key=f"update_{exc['id']}"):
                            try:
                                resp = requests.put(
                                    f"{API_URL}/exceptions/{exc['id']}",
                                    json={"reason": new_reason},
                                    headers=headers,
                                    timeout=5
                                )
                                if resp.status_code == 200:
                                    st.success("Motivo actualizado.")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Error actualizando excepción: {resp.text}")
                            except Exception as e:
                                st.error(f"Error conectando al backend: {e}")

                    with col4:
                        if st.button(f"🗑️ Eliminar", key=f"delete_{exc['id']}"):
                            try:
                                requests.delete(
                                    f"{API_URL}/exceptions/{exc['id']}",
                                    headers=headers,
                                    timeout=5
                                )
                                st.success("Excepción eliminada.")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error eliminando excepción: {e}")
            else:
                st.info("No hay excepciones registradas.")
        else:
            st.error("Error cargando excepciones.")
    except Exception as e:
        st.error(f"Error conectando al backend: {e}")
