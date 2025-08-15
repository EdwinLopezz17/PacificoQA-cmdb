# lib/io_utils.py
import pandas as pd
from io import BytesIO

def read_excel_xlsx(uploaded_file) -> pd.DataFrame:
    return pd.read_excel(uploaded_file)

def read_csv_smart(uploaded_file) -> pd.DataFrame:

    raw = uploaded_file.read() 
    tried = []

    def _try(enc, sep=None):
        try:
            return pd.read_csv(BytesIO(raw), encoding=enc, sep=sep, engine="python")
        except Exception as e:
            tried.append(f"{enc} / sep={repr(sep)} -> {e}")
            return None

    # Caso típico AD: UTF-16 con BOM
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        for sep in (None, "\t", ";", ","):
            df = _try("utf-16", sep)
            if df is not None:
                return df

    # Ronda general
    for enc in ("utf-8-sig", "cp1252", "latin1"):
        for sep in (None, "\t", ";", ","):
            df = _try(enc, sep)
            if df is not None:
                return df

    # Último intento: variantes de utf-16 explícitas
    for enc in ("utf-16le", "utf-16be"):
        for sep in (None, "\t", ";", ","):
            df = _try(enc, sep)
            if df is not None:
                return df

    # Si nada funcionó, levantamos un error legible
    detail = "\n".join(tried[-6:])  # últimas pruebas para no saturar
    raise ValueError(
        "No se pudo leer el CSV (encoding/separador desconocido). "
        "Reexporta como CSV UTF-8 o UTF-16 con separador coma o tab.\n"
        f"Últimos intentos:\n{detail}"
    )

def download_excel(df: pd.DataFrame, sheet_name: str, filename: str) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()
