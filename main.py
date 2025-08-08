# app.py
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="QA Inventario - Gestión de Activos", layout="wide")

TITLE = 'QA Inventario "Gestión de Activos"'
REQUIRED_COLS = [
    "Número de serie",
    "Hostname",
    "Tipo",
    "Correo Electrónico",
    "Clasificación Distribución",
]

def ui_sidebar():
    st.sidebar.header("⚙️ Validaciones a ejecutar")

    # Filtros base (opcional)
    with st.sidebar.expander("Filtros previos (dataset)", expanded=True):
        use_filter_dist = st.checkbox(
            "Incluir solo 'Distribuido(s)'", value=True,
            help="Filtra 'Clasificación Distribución' por 'distribuidos' o 'distribuido'."
        )
        use_filter_tipo = st.checkbox(
            "Incluir solo Notebook / Desktop", value=True,
            help="Filtra 'Tipo' por 'notebook' o 'desktop'."
        )

    # Parámetros
    with st.sidebar.expander("Parámetros", expanded=True):
        minlen_serie = st.number_input("Longitud mínima de Serie", min_value=1, value=7, step=1)
        minlen_host = st.number_input("Longitud mínima de Hostname", min_value=1, value=7, step=1)
        allowed_domains_raw = st.text_input(
            "Dominios de correo permitidos (separados por coma)",
            value="@pacifico,@prima",
            help="Se revisa que el correo contenga alguno de estos valores."
        )
        allowed_domains = [d.strip().lower() for d in allowed_domains_raw.split(",") if d.strip()]

    # Reglas: Serie
    with st.sidebar.expander("Validaciones: Número de serie", expanded=True):
        v_serie_vacio = st.checkbox("Serie vacía", value=True)
        v_serie_espacios = st.checkbox("Serie contiene espacios", value=True)
        v_serie_minlen = st.checkbox("Serie menor a longitud mínima", value=True)

    # Reglas: Hostname
    with st.sidebar.expander("Validaciones: Hostname", expanded=True):
        v_host_vacio = st.checkbox("Hostname vacío", value=True)
        v_host_espacios = st.checkbox("Hostname contiene espacios", value=True)
        v_host_minlen = st.checkbox("Hostname menor a longitud mínima", value=True)

    # Reglas: Correo
    with st.sidebar.expander("Validaciones: Correo", expanded=True):
        v_mail_vacio = st.checkbox("Correo vacío", value=True)
        v_mail_espacios = st.checkbox("Correo contiene espacios", value=True)
        v_mail_dominio = st.checkbox("Correo no pertenece a dominios permitidos", value=True)

    # Duplicados
    with st.sidebar.expander("Validaciones: Duplicados", expanded=True):
        v_dup_serie = st.checkbox("Serie duplicada", value=True)
        v_dup_host = st.checkbox("Hostname duplicado", value=True)
        v_dup_mail = st.checkbox("Correo duplicado", value=True)

    cfg = {
        "filters": {
            "dist": use_filter_dist,
            "tipo": use_filter_tipo,
        },
        "params": {
            "minlen_serie": minlen_serie,
            "minlen_host": minlen_host,
            "allowed_domains": allowed_domains,
        },
        "rules": {
            "serie": {"vacio": v_serie_vacio, "espacios": v_serie_espacios, "minlen": v_serie_minlen},
            "host":  {"vacio": v_host_vacio,  "espacios": v_host_espacios,  "minlen": v_host_minlen},
            "mail":  {"vacio": v_mail_vacio,  "espacios": v_mail_espacios,  "dominio": v_mail_dominio},
            "dups":  {"serie": v_dup_serie, "host": v_dup_host, "mail": v_dup_mail},
        },
    }
    return cfg

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    # Mantener solo columnas requeridas y hacer strip a strings
    df = df.copy()
    df = df[REQUIRED_COLS]
    df = df.apply(lambda col: col.map(lambda x: str(x).strip() if pd.notnull(x) else ""))
    return df

def apply_filters(df: pd.DataFrame, cfg) -> pd.DataFrame:
    f = cfg["filters"]

    if f["dist"]:
        df = df[df["Clasificación Distribución"].str.lower().isin(["distribuidos", "distribuido"])]

    if f["tipo"]:
        df = df[df["Tipo"].str.lower().isin(["notebook", "desktop"])]

    return df

def apply_validations(df: pd.DataFrame, cfg) -> pd.DataFrame:
    r = cfg["rules"]
    p = cfg["params"]

    df = df.copy()
    df["Alertas"] = ""

    # --- Serie ---
    if r["serie"]["vacio"]:
        df.loc[df["Número de serie"] == "", "Alertas"] += "Serie vacía. "
    if r["serie"]["espacios"]:
        df.loc[df["Número de serie"].str.contains(" "), "Alertas"] += "Serie contiene espacios. "
    if r["serie"]["minlen"]:
        df.loc[df["Número de serie"].str.len() < int(p["minlen_serie"]), "Alertas"] += "Serie menor a longitud mínima. "

    # --- Hostname ---
    if r["host"]["vacio"]:
        df.loc[df["Hostname"] == "", "Alertas"] += "Hostname vacío. "
    if r["host"]["espacios"]:
        df.loc[df["Hostname"].str.contains(" "), "Alertas"] += "Hostname contiene espacios. "
    if r["host"]["minlen"]:
        df.loc[df["Hostname"].str.len() < int(p["minlen_host"]), "Alertas"] += "Hostname menor a longitud mínima. "

    # --- Correo ---
    if r["mail"]["vacio"]:
        df.loc[df["Correo Electrónico"] == "", "Alertas"] += "Correo vacío. "
    if r["mail"]["espacios"]:
        df.loc[df["Correo Electrónico"].str.contains(" "), "Alertas"] += "Correo contiene espacios. "
    if r["mail"]["dominio"]:
        allowed = p["allowed_domains"]
        if allowed:
            mask_domain = ~df["Correo Electrónico"].str.lower().apply(
                lambda x: any(d in x for d in allowed)
            )
            df.loc[mask_domain, "Alertas"] += "Correo no pertenece a dominios permitidos. "

    # --- Duplicados ---
    if r["dups"]["serie"]:
        dup_serie = df["Número de serie"].duplicated(keep=False) & (df["Número de serie"] != "")
        df.loc[dup_serie, "Alertas"] += "Serie duplicada. "
    if r["dups"]["host"]:
        dup_host = df["Hostname"].duplicated(keep=False) & (df["Hostname"] != "")
        df.loc[dup_host, "Alertas"] += "Hostname duplicado. "
    if r["dups"]["mail"]:
        dup_mail = df["Correo Electrónico"].duplicated(keep=False) & (df["Correo Electrónico"] != "")
        df.loc[dup_mail, "Alertas"] += "Correo duplicado. "

    return df

def main():
    st.title(TITLE)
    st.write("Carga tu archivo de inventario en Excel y genera un reporte de **alertas** según reglas seleccionadas.")

    cfg = ui_sidebar()

    uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

    if uploaded_file is None:
        st.info("Esperando archivo .xlsx…")
        return

    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")
        return

    st.subheader("Columnas detectadas")
    st.write(df.columns.tolist())

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        st.error(f"Faltan columnas requeridas: {missing}")
        return

    # Normalizar y filtrar
    df = normalize_df(df)
    df = apply_filters(df, cfg)

    if df.empty:
        st.warning("Después de aplicar los filtros, no quedaron filas para validar.")
        return

    # Validaciones
    df_validado = apply_validations(df, cfg)
    df_alertas = df_validado[df_validado["Alertas"] != ""]

    st.subheader("Resultado")
    if not df_alertas.empty:
        st.success(f"Se encontraron {len(df_alertas)} filas con alertas.")
        st.dataframe(df_alertas, use_container_width=True)

        # Descargar Excel con alertas
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_alertas.to_excel(writer, index=False, sheet_name="Alertas")
        data = output.getvalue()

        st.download_button(
            label="📥 Descargar Excel con Alertas",
            data=data,
            file_name="alertas_QA_inventory.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.success("No se encontraron alertas. ¡Todo OK!")

if __name__ == "__main__":
    main()
