# Trazabilidad de muestras · defectos óseos

Prototipo para el curso **Sistemas de Información Hospitalarios II** (Magíster en Informática Médica,
Universidad de Chile, 2026). Construido con apoyo de IA.

> **Todos los datos son ficticios.** La investigación no está publicada; el prototipo no contiene
> números, notas ni imágenes reales del laboratorio.

## Problema

En un proyecto de investigación se generan defectos óseos en cráneos de ratón. Cada ratón pasa por
manejo (cirugía, sacrificio, decalcificación en EDTA), imagenología (microCT), procesamiento
histológico (desgaste, revisión, sets de corte, HE) y técnicas posteriores (IHQ/IF). Hoy la
información está fragmentada entre personas y registros. Ver [`docs/01_problema.md`](docs/01_problema.md).

## Qué hace

Aplicación web con un menú de 4 secciones:

| Sección | Para qué |
|---|---|
| 🐭 Ratones | Ficha de cada ratón: paso actual, último trabajo, dónde está el taco, placas en una tira de recuadros, manejo, imagenología e historial |
| 🧫 Manejo | Ratones en experimentación y en decalcificación; aviso **Cambiar EDTA** si pasan 3+ días sin cambio |
| 🔬 Histología | Ratones agrupados por paso del procesamiento |
| 🧪 Técnicas | Placas disponibles para IHQ/IF y resultados registrados |

Estado: **etapa 2 de 5** (solo consulta). Plan completo en [`docs/02_arquitectura.md`](docs/02_arquitectura.md).

## Cómo ejecutarlo

Requiere Python 3.10 o superior.

```bash
python3 -m venv .venv
source .venv/bin/activate          # en Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python3 generar_datos.py           # crea data/prototipo.db con 30 ratones ficticios
streamlit run app.py               # abre http://localhost:8501
```

## Archivos

| Archivo | Función |
|---|---|
| `app.py` | Pantallas (Streamlit). No toca la base de datos directamente. |
| `servicios.py` | Capa de lógica: único archivo que lee/escribe la base de datos. |
| `esquema.sql` | Tablas de la base de datos (SQLite). |
| `generar_datos.py` | Genera los datos ficticios según las reglas del laboratorio. |
| `data/prototipo.db` | Base de datos generada. |
| `docs/` | Problema, decisiones de arquitectura y sus razones. |
| `CLAUDE.md` | Reglas para el asistente de IA usado en el desarrollo. |

## Decisiones principales

- **Interfaz y lógica separadas** (`app.py` / `servicios.py`), siguiendo la idea de una capa intermedia que valida y protege los datos.
- **Base relacional** (ratón → bloque → placa → resultado). SQLite en desarrollo; PostgreSQL (Supabase) al publicar.
- **Costo cero**: publicación prevista en Streamlit Community Cloud + Supabase (plan gratuito, sin tarjeta).
- **Trazabilidad**: cada acción queda como evento (quién, qué, cuándo).
