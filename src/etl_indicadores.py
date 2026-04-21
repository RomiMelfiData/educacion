"""
Educacion — ETL de Indicadores Educativos
==========================================
Autora: Romina Melfi
Descripción:
    Procesa los archivos de datos abiertos del Ministerio de Educación
    de la Nación Argentina y genera CSVs limpios con los KPIs educativos
    listos para importar en Power BI.

Fuentes de datos:
    Ministerio de Educación de la Nación — datos.gob.ar
    https://www.datos.gob.ar/dataset/educacion-base-datos-por-escuela-2024

Archivos de entrada:
    - 2024_Trayectoria__agregadain.csv      → Repitencia, Abandono, Promoción
    - 2024_Matricula_por_edad__agregadain.csv → Sobreedad
    - 2024_Cargos__agregadain.csv            → Cobertura docente

Archivos de salida (en data/processed/):
    - kpis_trayectoria_2024.csv
    - sobreedad_2024.csv
    - cobertura_docente_2024.csv

Uso:
    python src/etl_indicadores.py
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE RUTAS
# ─────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Archivos de entrada esperados en data/raw/
ARCHIVO_TRAYECTORIA  = RAW_DIR / "2024_Trayectoria__agregadain.csv"
ARCHIVO_MATRICULA    = RAW_DIR / "2024_Matricula_por_edad__agregadain.csv"
ARCHIVO_CARGOS       = RAW_DIR / "2024_Cargos__agregadain.csv"

# Columnas de identificación comunes a todos los archivos
COLS_ID = ["provincia", "Departamento", "sector", "ambito"]

# Año de referencia del relevamiento
ANIO = 2024

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def cargar_csv(ruta: Path) -> pd.DataFrame:
    """Carga un CSV del Ministerio con separador ; y tipado str."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}\n"
            f"Descargalo desde: https://www.datos.gob.ar/dataset/educacion-base-datos-por-escuela-2024"
        )
    df = pd.read_csv(ruta, sep=";", dtype=str, encoding="utf-8")
    print(f"  OK {ruta.name} — {len(df):,} filas, {len(df.columns)} columnas")
    return df


def a_numerico(df: pd.DataFrame, excluir: list) -> pd.DataFrame:
    """Convierte todas las columnas excepto las de identificación a numérico."""
    cols_num = [c for c in df.columns if c not in excluir]
    df[cols_num] = df[cols_num].apply(pd.to_numeric, errors="coerce")
    return df


def tasa(numerador, denominador) -> float:
    """Calcula una tasa porcentual con manejo de división por cero."""
    if denominador and denominador > 0:
        return round(numerador / denominador * 100, 2)
    return None


# ─────────────────────────────────────────────
# ETL 1 — TRAYECTORIA (Repitencia, Abandono, Promoción)
# ─────────────────────────────────────────────

def procesar_trayectoria() -> pd.DataFrame:
    """
    Calcula tasas de repitencia, abandono y promoción efectiva
    por provincia, departamento, sector, ámbito y nivel educativo.

    Fuente de cálculo:
        - Repitencia       = no_promovidos / matricula_inicial × 100
        - Abandono         = salidos_sin_pase / matricula_inicial × 100
        - Promoción Ef.    = promovidos / ultimo_anio_inscripto × 100

    Estructura 6-6 (nacional homogénea):
        Primaria   → grados 1 a 6
        Secundaria → grados 7 a 12
    """
    print("\n[1/3] Procesando trayectoria...")
    df = cargar_csv(ARCHIVO_TRAYECTORIA)
    df = a_numerico(df, COLS_ID)

    # Grados por nivel según estructura nacional 6-6
    GRADOS_PRIMARIA   = [str(i) for i in range(1, 7)]
    GRADOS_SECUNDARIA = [str(i) for i in range(7, 13)]

    def sumar_grados(row, prefijo, grados):
        return sum(row.get(f"{prefijo}_{g}", 0) or 0 for g in grados)

    filas = []
    for _, row in df.iterrows():
        base = {
            "anio":         ANIO,
            "provincia":    row["provincia"],
            "departamento": row["Departamento"],
            "sector":       row["sector"],
            "ambito":       row["ambito"],
        }
        for nivel, grados in [("Primaria", GRADOS_PRIMARIA), ("Secundaria", GRADOS_SECUNDARIA)]:
            matricula_ini = sumar_grados(row, "inicial",    grados)
            promovidos    = sumar_grados(row, "promovidos", grados)
            no_promovidos = sumar_grados(row, "nopromo",    grados)
            salidos_ssp   = sumar_grados(row, "ssp",        grados)
            ultimo_anio   = sumar_grados(row, "ultimo",     grados)

            if matricula_ini > 0:
                filas.append({
                    **base,
                    "nivel":               nivel,
                    "matricula_inicial":   int(matricula_ini),
                    "promovidos":          int(promovidos),
                    "no_promovidos":       int(no_promovidos),
                    "salidos_sin_pase":    int(salidos_ssp),
                    "ultimo_anio_inscripto": int(ultimo_anio),
                    "tasa_repitencia":     tasa(no_promovidos, matricula_ini),
                    "tasa_abandono":       tasa(salidos_ssp,   matricula_ini),
                    "tasa_promocion_ef":   tasa(promovidos,    ultimo_anio),
                })

    resultado = pd.DataFrame(filas)
    salida = OUT_DIR / "kpis_trayectoria_2024.csv"
    resultado.to_csv(salida, index=False, encoding="utf-8")
    print(f"  OK Guardado: {salida.name} — {len(resultado):,} filas")
    return resultado


# ─────────────────────────────────────────────
# ETL 2 — MATRÍCULA POR EDAD (Sobreedad)
# ─────────────────────────────────────────────

def procesar_sobreedad() -> pd.DataFrame:
    """
    Calcula la tasa de sobreedad por grado, provincia, sector y ámbito.

    Definición:
        Alumno con sobreedad = tiene 2 o más años sobre la edad
        teórica esperada para su grado (según estructura nacional 6-6).

    Tasa de sobreedad = alumnos_con_sobreedad / matricula_total × 100
    """
    print("\n[2/3] Procesando sobreedad...")
    df = cargar_csv(ARCHIVO_MATRICULA)

    # Edad teórica esperada por grado (estructura 6-6)
    EDAD_ESPERADA = {
        "1°": 6,  "2°": 7,  "3°": 8,  "4°": 9,  "5°": 10, "6°": 11,
        "7°": 12, "8°": 13, "9°": 14, "10°": 15, "11°": 16, "12°": 17,
        "Sala de 3": 3, "Sala de 4": 4, "Sala de 5": 5,
    }

    # Mapeo de columnas de edad en el CSV
    def col_edad(i):
        return "1año" if i == 1 else f"{i}años"

    # Convertir columnas de edad a numérico
    for i in range(0, 30):
        col = col_edad(i)
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    filas = []
    for _, row in df.iterrows():
        grado = str(row["grado"]).strip()
        edad_esp = EDAD_ESPERADA.get(grado)
        if edad_esp is None:
            continue  # Omitir grados especiales (SNU, Lactantes, etc.)

        total = sum(float(row.get(col_edad(i), 0) or 0) for i in range(0, 30)
                    if col_edad(i) in row.index)
        sobreedad = sum(float(row.get(col_edad(i), 0) or 0)
                        for i in range(edad_esp + 2, 30)
                        if col_edad(i) in row.index)

        if total > 0:
            filas.append({
                "anio":             ANIO,
                "provincia":        row["provincia"],
                "departamento":     row["Departamento"],
                "sector":           row["sector"],
                "ambito":           row["ambito"],
                "grado":            grado,
                "matricula_total":  int(total),
                "alumnos_sobreedad": int(sobreedad),
                "tasa_sobreedad":   tasa(sobreedad, total),
            })

    resultado = pd.DataFrame(filas)
    salida = OUT_DIR / "sobreedad_2024.csv"
    resultado.to_csv(salida, index=False, encoding="utf-8")
    print(f"  OK Guardado: {salida.name} — {len(resultado):,} filas")
    return resultado


# ─────────────────────────────────────────────
# ETL 3 — CARGOS (Cobertura Docente)
# ─────────────────────────────────────────────

def procesar_cobertura_docente() -> pd.DataFrame:
    """
    Calcula la tasa de cobertura de cargos docentes por nivel educativo.

    Columnas del CSV (nomenclatura del Ministerio):
        ini_ = Inicial   | pri_ = Primaria
        sec_ = Secundaria | snu_ = Superior No Universitario
        _dir = Directivos | _fte = Frente a curso | _apo = Apoyo
        _cub = Cubiertos  | _ncub = No cubiertos

    Tasa de cobertura = cargos_cubiertos / (cubiertos + no_cubiertos) × 100
    """
    print("\n[3/3] Procesando cobertura docente...")
    df = cargar_csv(ARCHIVO_CARGOS)
    df = a_numerico(df, COLS_ID)

    # Prefijos de nivel y sus etiquetas legibles
    NIVELES = {
        "ini": "Inicial",
        "pri": "Primaria",
        "sec": "Secundaria",
    }

    # Tipos de cargo por nivel
    TIPOS_CARGO = {
        "ini": ["dir", "fte", "apo"],
        "pri": ["dir", "fte", "apo"],
        "sec": ["dir", "fte", "apo"],
    }

    filas = []
    for _, row in df.iterrows():
        base = {
            "anio":         ANIO,
            "provincia":    row["provincia"],
            "departamento": row["Departamento"],
            "sector":       row["sector"],
            "ambito":       row["ambito"],
        }
        for prefijo, nivel_label in NIVELES.items():
            tipos = TIPOS_CARGO[prefijo]
            cubiertos   = sum(row.get(f"{prefijo}_{t}_cub",  0) or 0 for t in tipos)
            no_cubiertos = sum(row.get(f"{prefijo}_{t}_ncub", 0) or 0 for t in tipos)
            total_cargos = cubiertos + no_cubiertos

            if total_cargos > 0:
                filas.append({
                    **base,
                    "nivel":            nivel_label,
                    "cargos_cubiertos": int(cubiertos),
                    "cargos_vacantes":  int(no_cubiertos),
                    "total_cargos":     int(total_cargos),
                    "tasa_cobertura":   tasa(cubiertos, total_cargos),
                })

    resultado = pd.DataFrame(filas)
    salida = OUT_DIR / "cobertura_docente_2024.csv"
    resultado.to_csv(salida, index=False, encoding="utf-8")
    print(f"  OK Guardado: {salida.name} — {len(resultado):,} filas")
    return resultado


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Educacion — ETL de Indicadores Educativos 2024")
    print("=" * 55)
    print(f"  Entrada : {RAW_DIR}")
    print(f"  Salida  : {OUT_DIR}")
    print("=" * 55)

    df_tray = procesar_trayectoria()
    df_sob  = procesar_sobreedad()
    df_cob  = procesar_cobertura_docente()

    print("\n" + "=" * 55)
    print("  Resumen del procesamiento")
    print("=" * 55)

    for label, df in [
        ("Trayectoria (repitencia/abandono/promocion)", df_tray),
        ("Sobreedad", df_sob),
        ("Cobertura docente", df_cob),
    ]:
        privado = df[df["sector"] == "Privado"]
        print(f"\n  {label}")
        print(f"    Total filas     : {len(df):>7,}")
        print(f"    Sector Privado  : {len(privado):>7,}")
        print(f"    Provincias      : {df['provincia'].nunique():>7}")

    print("\n  OK ETL completado. Archivos listos para Power BI.")
    print("=" * 55)


if __name__ == "__main__":
    main()
