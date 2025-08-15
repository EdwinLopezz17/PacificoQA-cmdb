# pages/active_Directory.py
import streamlit as st
import pandas as pd

from lib.cmdb_utils import normalize_cmdb
from lib.compare_ad import normalize_ad, compare_cmdb_ad
from lib.io_utils import read_excel_xlsx, read_csv_smart, download_excel

st.set_page_config(page_title="CMDB vs Active Directory", layout="wide")

st.title("CMDB vs Active Directory (Pacífico + Prima)")
st.write("""
Sube la **CMDB (.xlsx)** (solo se usan equipos *Distribuido(s)*) y los **dos exports de AD (.csv)**:
- AD Pacífico Seguros (`EmailAddress`, `Enabled`)
- AD Prima AFP (`EmailAddress`, `Enabled`)

Se combinarán y se validará por correo.
""")

cmdb_file = st.file_uploader("CMDB (.xlsx)", type=["xlsx"], key="cmdb_ad")

st.subheader("Archivos de Active Directory (CSV)")
col1, col2 = st.columns(2)
with col1:
    ad_file_pacifico = st.file_uploader("AD Pacífico (.csv)", type=["csv"], key="ad_pacifico")
with col2:
    ad_file_prima = st.file_uploader("AD Prima (.csv)", type=["csv"], key="ad_prima")

if cmdb_file and ad_file_pacifico and ad_file_prima:
    try:
        # --- CMDB ---
        df_cmdb_raw = read_excel_xlsx(cmdb_file)
        df_cmdb = normalize_cmdb(df_cmdb_raw)  # ya filtra Distribuido(s)

        if "Correo Electrónico" not in df_cmdb.columns:
            raise ValueError("La CMDB no tiene la columna 'Correo Electrónico'")

        cmdb_emails = (
            df_cmdb[["Correo Electrónico"]]
            .rename(columns={"Correo Electrónico": "email"})
            .assign(email=lambda s: s["email"].map(lambda x: str(x).strip().lower()))
            .drop_duplicates()
        )

        # --- AD: leer, normalizar cada uno y combinar ---
        ad_pac_raw = read_csv_smart(ad_file_pacifico)
        ad_pri_raw = read_csv_smart(ad_file_prima)

        ad_pac_std = normalize_ad(ad_pac_raw)  # -> email, enabled
        ad_pri_std = normalize_ad(ad_pri_raw)

        # (opcional) rastro de origen
        ad_pac_std["origen"] = "pacifico"
        ad_pri_std["origen"] = "prima"

        ad_all = pd.concat([ad_pac_std, ad_pri_std], ignore_index=True)

        # Deduplicar por email si aparece en ambos (nos quedamos con el primero)
        ad_all = ad_all.drop_duplicates(subset=["email"], keep="first")

        st.subheader("Muestras normalizadas")
        st.write("**CMDB (emails)**", cmdb_emails.head(10))
        st.write("**AD combinado (std)**", ad_all.head(10))

        # --- Comparación ---
        result = compare_cmdb_ad(cmdb_emails, ad_all)

        st.subheader("Resultado de la comparación")
        st.dataframe(result, use_container_width=True)

        alerts = result[result["Alertas"] != ""].copy()
        st.write(f"**Filas con alertas**: {len(alerts)}")
        if not alerts.empty:
            data = download_excel(alerts, "Alertas_AD", "alertas_cmdb_ad_combinado.xlsx")
            st.download_button(
                "📥 Descargar Excel de Alertas (AD combinado)",
                data=data,
                file_name="alertas_cmdb_ad_combinado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Error procesando archivos: {e}")
else:
    st.info("Sube la CMDB y ambos CSV de AD para iniciar la comparación.")
