# pages/intune.py
import streamlit as st
import pandas as pd

from lib.cmdb_utils import normalize_cmdb, cmdb_std_cols
from lib.compare_intune import normalize_intune, compare_cmdb_intune
from lib.io_utils import read_excel_xlsx, read_csv_smart, download_excel

st.set_page_config(page_title="CMDB vs Intune", layout="wide")

st.title("🔄 CMDB vs Intune (Pacífico + Prima)")
st.write("""
Sube la **CMDB (.xlsx)** y los **dos reportes de Intune (.csv)**:
- Intune Pacífico Seguros
- Intune Prima AFP

Se combinarán y se compararán contra CMDB por **Número de serie**.
""")

cmdb_file = st.file_uploader("CMDB (.xlsx)", type=["xlsx"], key="cmdb_intune")

st.subheader("Archivos de Intune (.csv)")
col1, col2 = st.columns(2)
with col1:
    intune_file_pacifico = st.file_uploader("Intune Pacífico (.csv)", type=["csv"], key="intune_pacifico")
with col2:
    intune_file_prima = st.file_uploader("Intune Prima (.csv)", type=["csv"], key="intune_prima")

if cmdb_file and intune_file_pacifico and intune_file_prima:
    try:
        # --- CMDB ---
        df_cmdb_raw = read_excel_xlsx(cmdb_file)
        df_cmdb = normalize_cmdb(df_cmdb_raw)        # filtra Distribuido(s) y normaliza
        df_cmdb_std = cmdb_std_cols(df_cmdb)         # -> serial, email, hostname

        # --- INTUNE: leer, normalizar cada uno y combinar ---
        pac_raw = read_csv_smart(intune_file_pacifico)
        pri_raw = read_csv_smart(intune_file_prima)

        pac_std = normalize_intune(pac_raw)          # -> serial, email, hostname
        pri_std = normalize_intune(pri_raw)

        # (opcional) dejar rastro de origen
        pac_std["origen"] = "pacifico"
        pri_std["origen"] = "prima"

        intune_all = pd.concat([pac_std, pri_std], ignore_index=True)

        # Deduplicar por serial si aparece en ambas consolas (nos quedamos con el primero)
        intune_all = intune_all.drop_duplicates(subset=["serial"], keep="first")

        st.subheader("Muestras normalizadas")
        st.write("**CMDB (std)**", df_cmdb_std.head(10))
        st.write("**Intune combinado (std)**", intune_all.head(10))

        # --- Comparación ---
        result = compare_cmdb_intune(df_cmdb_std, intune_all)

        st.subheader("Resultado de la comparación")
        st.dataframe(result, use_container_width=True)

        alerts = result[result["Alertas"] != ""].copy()
        st.write(f"**Filas con alertas**: {len(alerts)}")
        if not alerts.empty:
            data = download_excel(alerts, "Alertas_Intune", "alertas_cmdb_intune_combinado.xlsx")
            st.download_button(
                "📥 Descargar Excel de Alertas (Intune combinado)",
                data=data,
                file_name="alertas_cmdb_intune_combinado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Error procesando archivos: {e}")
else:
    st.info("Sube la CMDB y ambos CSV de Intune para iniciar la comparación.")
