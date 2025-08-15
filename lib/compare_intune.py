# lib/compare_intune.py
import pandas as pd

INTUNE_REQUIRED = ["Serial number", "Primary user UPN", "Device name"]

def normalize_intune(df: pd.DataFrame) -> pd.DataFrame:
    faltantes = [c for c in INTUNE_REQUIRED if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en Intune: {faltantes}")

    df = df.copy()
    for c in INTUNE_REQUIRED:
        df[c] = df[c].map(lambda x: str(x).strip() if pd.notnull(x) else "")

    df_std = df.rename(columns={
        "Serial number": "serial",
        "Primary user UPN": "email",
        "Device name": "hostname"
    })[["serial", "email", "hostname"]]

    df_std["serial"] = df_std["serial"]
    df_std["email"] = df_std["email"].str.lower()
    df_std["hostname"] = df_std["hostname"].str.lower()

    return df_std

def compare_cmdb_intune(cmdb_std: pd.DataFrame, intune_std: pd.DataFrame) -> pd.DataFrame:

    left = cmdb_std.copy()
    left["email"] = left["email"].str.lower()
    left["hostname"] = left["hostname"].str.lower()

    dup_cmdb = left.duplicated(subset=["serial"], keep=False)
    dup_intune = intune_std.duplicated(subset=["serial"], keep=False)

    #vista previa
    intune_first = intune_std.drop_duplicates(subset=["serial"], keep="first")

    merged = left.merge(intune_first, on="serial", how="left", suffixes=("_cmdb", "_intune"), indicator=True)

    def build_alert(row):
        alerts = []
        if row["_merge"] == "left_only":
            alerts.append("Serie no existe en Intune")
        else:
            if row["email_cmdb"] and row["email_intune"] and row["email_cmdb"] != row["email_intune"]:
                alerts.append("Correo no coincide")
            if row["hostname_cmdb"] and row["hostname_intune"] and row["hostname_cmdb"] != row["hostname_intune"]:
                alerts.append("Hostname no coincide")
        return "; ".join(alerts)

    merged["Alertas"] = merged.apply(build_alert, axis=1)

    # duplicados
    merged["Duplicado en CMDB (serial)"] = merged["serial"].isin(left.loc[dup_cmdb, "serial"])
    merged["Duplicado en Intune (serial)"] = merged["serial"].isin(intune_std.loc[dup_intune, "serial"])

    cols = [
        "serial",
        "email_cmdb", "email_intune",
        "hostname_cmdb", "hostname_intune",
        "Duplicado en CMDB (serial)", "Duplicado en Intune (serial)",
        "Alertas"
    ]
    return merged[cols]

