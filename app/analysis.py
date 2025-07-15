import streamlit as st
import pandas as pd
from io import BytesIO
import requests

API_URL = "http://localhost:3001/api"

def run_analysis():
    st.title("📊 QA Inventory Analyzer")

    uploaded_file = st.file_uploader("📁 Sube tu archivo Excel", type=["xlsx"])

    if uploaded_file is not None:
        token = st.session_state.get("token", "")
        headers = {"Authorization": f"Bearer {token}"}

        # Cargar excepciones desde el backend
        try:
            resp = requests.get(f"{API_URL}/exceptions", headers=headers, timeout=5)
            if resp.status_code == 200:
                excepciones = resp.json()
                excepciones_series = [e["serie"].strip() for e in excepciones]
            else:
                st.error("Error cargando excepciones.")
                return
        except Exception as e:
            st.error(f"Error conectando al backend: {e}")
            return

        try:
            df = pd.read_excel(uploaded_file)

            st.subheader("Columnas encontradas en el archivo:")
            st.write(df.columns.tolist())

            cols = [
                'Número de serie',
                'Hostname',
                'Tipo',
                'Correo Electrónico',
                'Clasificación Distribución'
            ]

            missing_cols = [c for c in cols if c not in df.columns]
            if missing_cols:
                st.error(f"⚠️ Faltan columnas: {missing_cols}")
                return

            df = df[cols]
            df = df.apply(lambda col: col.map(lambda x: str(x).strip() if pd.notnull(x) else ""))

            df = df[df['Clasificación Distribución'].str.lower().isin(['distribuidos', 'distribuido'])]
            df = df[df['Tipo'].str.lower().isin(['notebook', 'desktop'])]

            # Excluir excepciones
            df = df[~df['Número de serie'].isin(excepciones_series)]

            df["Alertas"] = ""

            # reglas de serie
            df.loc[df['Número de serie'] == "", "Alertas"] += "Serie vacía. "
            df.loc[df['Número de serie'].str.contains(" "), "Alertas"] += "Serie contiene espacios. "
            df.loc[df['Número de serie'].str.len() < 7, "Alertas"] += "Serie menor a 7 caracteres. "

            # reglas de hostname
            df.loc[df['Hostname'] == "", "Alertas"] += "Hostname vacío. "
            df.loc[df['Hostname'].str.contains(" "), "Alertas"] += "Hostname contiene espacios. "
            df.loc[df['Hostname'].str.len() < 7, "Alertas"] += "Hostname menor a 7 caracteres. "

            # reglas Correo
            df.loc[df['Correo Electrónico'] == "", "Alertas"] += "Correo vacío. "
            df.loc[df['Correo Electrónico'].str.contains(" "), "Alertas"] += "Correo contiene espacios. "
            df.loc[
                ~df['Correo Electrónico'].str.lower().str.contains("@pacifico|@prima"),
                "Alertas"
            ] += "Correo no pertenece a @pacifico o @prima. "

            # detectar duplicados
            duplicados_serie = df['Número de serie'].duplicated(keep=False) & (df['Número de serie'] != "")
            df.loc[duplicados_serie, "Alertas"] += "Serie duplicada. "

            duplicados_hostname = df['Hostname'].duplicated(keep=False) & (df['Hostname'] != "")
            df.loc[duplicados_hostname, "Alertas"] += "Hostname duplicado. "

            duplicados_correo = df['Correo Electrónico'].duplicated(keep=False) & (df['Correo Electrónico'] != "")
            df.loc[duplicados_correo, "Alertas"] += "Correo duplicado. "

            df_alertas = df[df["Alertas"] != ""]

            if not df_alertas.empty:
                st.success(f"Se encontraron {len(df_alertas)} filas con alertas.")
                st.dataframe(df_alertas, use_container_width=True)

                # download
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_alertas.to_excel(writer, index=False, sheet_name='Alertas')
                data = output.getvalue()

                st.download_button(
                    label="Descargar Excel con Alertas",
                    data=data,
                    file_name="alertas_QA_inventory.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.success("No se encontraron alertas. ¡Todo OK!")

        except Exception as e:
            st.error(f"Error procesando archivo: {e}")
