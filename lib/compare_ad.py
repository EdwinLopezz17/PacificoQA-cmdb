# lib/compare_ad.py
import pandas as pd

AD_REQUIRED = ["EmailAddress", "Enabled"]

def normalize_ad(df: pd.DataFrame) -> pd.DataFrame:
    faltantes = [c for c in AD_REQUIRED if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en Active Directory: {faltantes}")

    df = df.copy()
    df["EmailAddress"] = df["EmailAddress"].map(lambda x: str(x).strip().lower() if pd.notnull(x) else "")

    #meapeamos estado
    def to_bool(v):
        s = str(v).strip().lower()
        if s in ("true", "1", "yes", "y", "enabled","verdadero"):
            return True
        if s in ("false", "0", "no", "n", "disabled","falso"):
            return False
        return None  # desconocido
    df["Enabled"] = df["Enabled"].map(to_bool)
    return df.rename(columns={"EmailAddress": "email", "Enabled": "enabled"})[["email", "enabled"]]

def compare_cmdb_ad(cmdb_emails: pd.DataFrame, ad_std: pd.DataFrame) -> pd.DataFrame:

    cm = cmdb_emails.copy()
    cm["email"] = cm["email"].str.lower()

    merged = cm.merge(ad_std, on="email", how="left", indicator=True)

    def build_alert(row):
        if row["_merge"] == "left_only":
            return "Correo no existe en AD"
        if row["enabled"] is False:
            return "Cuenta deshabilitada en AD"
        if row["enabled"] is None:
            return "Estado Enabled desconocido en AD"
        return ""

    merged["Alertas"] = merged.apply(build_alert, axis=1)
    return merged[["email", "enabled", "Alertas"]]

