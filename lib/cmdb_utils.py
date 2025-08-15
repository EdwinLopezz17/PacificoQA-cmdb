# lib/cmdb_utils.py
import pandas as pd

CMDB_REQUIRED_MIN = ["Número de serie", "Correo Electrónico", "Hostname", "Clasificación Distribución"]

def normalize_cmdb(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    faltantes = [c for c in CMDB_REQUIRED_MIN if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en CMDB: {faltantes}")

    for c in CMDB_REQUIRED_MIN:
        df[c] = df[c].map(lambda x: str(x).strip() if pd.notnull(x) else "")

    df = df[df["Clasificación Distribución"].str.lower().isin(["distribuido", "distribuidos"])]

    return df

def cmdb_std_cols(df: pd.DataFrame) -> pd.DataFrame:

    return df.rename(columns={
        "Número de serie": "serial",
        "Correo Electrónico": "email",
        "Hostname": "hostname"
    })[["serial", "email", "hostname"]]

