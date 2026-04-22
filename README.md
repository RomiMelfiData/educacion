# Educacion 📊

**Tablero de Indicadores Educativos para Escuelas Privadas de Argentina**

> Proyecto personal de Romina Melfi — Data Analyst en transición desde la docencia.

---

## ¿Qué es Educacion?

Educacion es un pipeline de datos + tablero Power BI que transforma los datos abiertos del Ministerio de Educación de la Nación en indicadores accionables para directivos de escuelas privadas.

Permite ver — de forma simple y visual — cómo está el sector privado en términos de:

- 📉 Tasa de Abandono Interanual
- 🔁 Tasa de Repitencia
- ✅ Tasa de Promoción Efectiva
- 🎂 Tasa de Sobreedad (por grado)
- 👩‍🏫 Cobertura de Cargos Docentes
- 📈 Evolución de Matrícula Privada

Todo desagregado por **provincia**, **departamento**, **sector** (Privado/Estatal) y **ámbito** (Urbano/Rural).

---

## Estructura del repositorio

```
educacion/
├── src/
│   └── etl_indicadores.py     # Script ETL principal
├── data/
│   ├── raw/                   # Archivos originales del Ministerio (no se suben al repo)
│   └── processed/             # CSVs limpios generados por el ETL
├── docs/
│   ├── Educacion_Brief.docx       # Product brief del proyecto
│   └── Educacion_Bitacora.docx    # Registro de decisiones
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Fuentes de datos

Todos los datos son **públicos y abiertos**, publicados por el Ministerio de Educación de la Nación.

| Archivo | Descripción | Enlace |
|---|---|---|
| `2024_Trayectoria__agregadain.csv` | Promovidos, repitentes, salidos sin pase por grado | [datos.gob.ar](https://www.datos.gob.ar/dataset/educacion-base-datos-por-escuela-2024) |
| `2024_Matricula_por_edad__agregadain.csv` | Matrícula por edad y sección | [datos.gob.ar](https://www.datos.gob.ar/dataset/educacion-base-datos-por-escuela-2024) |
| `2024_Cargos__agregadain.csv` | Cargos docentes cubiertos y no cubiertos | [datos.gob.ar](https://www.datos.gob.ar/dataset/educacion-base-datos-por-escuela-2024) |
| XLSX Tasas 2012–2024 | Series históricas de abandono, repitencia, promoción, sobreedad | [argentina.gob.ar](https://www.argentina.gob.ar/educacion/evaluacion-e-informacion-educativa/indicadores) |

---

## Cómo usar

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/educacion.git
cd educacion
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Descargar los datos crudos

Descargá los archivos CSV desde [datos.gob.ar](https://www.datos.gob.ar/dataset/educacion-base-datos-por-escuela-2024) y copiá los siguientes archivos en la carpeta `data/raw/`:

```
data/raw/
├── 2024_Trayectoria__agregadain.csv
├── 2024_Matricula_por_edad__agregadain.csv
└── 2024_Cargos__agregadain.csv
```

### 4. Ejecutar el ETL

```bash
python src/etl_indicadores.py
```

Los archivos procesados se generan automáticamente en `data/processed/`:

```
data/processed/
├── kpis_trayectoria_2024.csv    # Repitencia, abandono, promoción por provincia/sector
├── sobreedad_2024.csv           # Sobreedad por grado, provincia y sector
└── cobertura_docente_2024.csv   # Cargos cubiertos/vacantes por nivel
```

### 5. Importar en Power BI

Importá los tres CSVs de `data/processed/` en Power BI Desktop como fuentes de datos y conectalos al modelo estrella definido en el tablero.

---

## Outputs del ETL

### `kpis_trayectoria_2024.csv`

| Columna | Descripción |
|---|---|
| `anio` | Año del relevamiento (2024) |
| `provincia` | Jurisdicción |
| `departamento` | Departamento/partido |
| `sector` | Privado / Estatal |
| `ambito` | Urbano / Rural |
| `nivel` | Primaria / Secundaria |
| `matricula_inicial` | Alumnos al inicio del año lectivo |
| `promovidos` | Alumnos promovidos al año siguiente |
| `no_promovidos` | Alumnos que repitieron |
| `salidos_sin_pase` | Alumnos que abandonaron |
| `tasa_repitencia` | % repitentes sobre matrícula inicial |
| `tasa_abandono` | % abandonaron sobre matrícula inicial |
| `tasa_promocion_ef` | % promovidos sobre último año inscripto |

### `sobreedad_2024.csv`

| Columna | Descripción |
|---|---|
| `grado` | Grado escolar (1° a 12°, Salas 3-4-5) |
| `matricula_total` | Total de alumnos en ese grado |
| `alumnos_sobreedad` | Alumnos con 2+ años sobre la edad esperada |
| `tasa_sobreedad` | % alumnos con sobreedad |

### `cobertura_docente_2024.csv`

| Columna | Descripción |
|---|---|
| `nivel` | Inicial / Primaria / Secundaria |
| `cargos_cubiertos` | Cargos con titular o suplente |
| `cargos_vacantes` | Cargos sin cobertura |
| `tasa_cobertura` | % de cargos cubiertos |

---

## Tecnologías utilizadas

- **Python 3.10+** — ETL y procesamiento de datos
- **pandas** — Manipulación y transformación de datos
- **Power BI Desktop** — Modelado y visualización
- **Power BI Service** — Publicación y distribución

---

## Roadmap

- [x] Exploración y diagnóstico de fuentes de datos
- [x] ETL: cálculo de KPIs de trayectoria, sobreedad y cobertura docente
- [ ] Modelo estrella en Power BI Desktop
- [ ] Medidas DAX para los 6 KPIs
- [ ] 5 páginas del tablero (Resumen, Trayectorias, Sobreedad, Docentes, Mapa)
- [ ] Publicación en Power BI Service (demo público)
- [ ] Primera venta / piloto con escuela privada

---

## Autora

**Romina Melfi** — Data Analyst en transición desde la docencia  
📍 Argentina  
🔗 [LinkedIn](https://linkedin.com/in/TU_PERFIL)

---

## Licencia

Los datos utilizados son públicos y están bajo licencia [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) del Ministerio de Educación de la Nación Argentina.

El código de este repositorio está disponible bajo licencia MIT.
