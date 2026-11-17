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

Estado: **etapa 4 de 5** (login por rol, registro de acciones y publicación en la nube).

**Usuarios de prueba** (contraseña `demo123`): Javiera (histología), Docente responsable,
Estudiante A, B y C.

| Rol | Registra |
|---|---|
| Histología | Inclusión/reinclusión, pares de desgaste, corte de set, tinción HE, archivo, ubicaciones, técnicas |
| Docente | Sacrificio, revisión SA, envío a histología |
| Estudiante | Cambios de EDTA, envío a histología, técnicas en placas (IHQ/IF u otra), ubicación de placas | Plan completo en [`docs/02_arquitectura.md`](docs/02_arquitectura.md).

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
| `subir_a_supabase.py` | Copia la base local a PostgreSQL en Supabase (para publicar). |
| `data/prototipo.db` | Base de datos generada. |
| `docs/` | Problema, decisiones de arquitectura y sus razones. |
| `CLAUDE.md` | Reglas para el asistente de IA usado en el desarrollo. |

## Decisiones principales

- **Interfaz y lógica separadas** (`app.py` / `servicios.py`), siguiendo la idea de una capa intermedia que valida y protege los datos.
- **Base relacional** (ratón → bloque → placa → resultado). SQLite en desarrollo; PostgreSQL (Supabase) al publicar.
- **Costo cero**: publicación prevista en Streamlit Community Cloud + Supabase (plan gratuito, sin tarjeta).
- **Trazabilidad**: cada acción queda como evento (quién, qué, cuándo).

## Publicar (Supabase + Streamlit Community Cloud, costo cero)

La app usa **SQLite local** si no hay configuración, y **PostgreSQL (Supabase)** si existe
`DATABASE_URL` en `.streamlit/secrets.toml`. La contraseña nunca va en el código ni en GitHub.

1. **Supabase**: crear proyecto → botón **Connect** → copiar la conexión **Session pooler**
   (URI). Reemplazar `[YOUR-PASSWORD]` por la contraseña del proyecto.
2. Crear el archivo `.streamlit/secrets.toml` con la línea `DATABASE_URL = "..."`.
3. Subir los datos ficticios: `python3 generar_datos.py && python3 subir_a_supabase.py`
4. **Streamlit Community Cloud** (share.streamlit.io): *Create app* → repositorio → archivo
   `app.py` → *Advanced settings* → Python 3.12 → en **Secrets** pegar la misma línea `DATABASE_URL = "..."`.
5. En la app, la barra lateral indica qué base se está usando.

Notas del plan gratuito: la app se "duerme" tras horas sin uso (despierta al entrar) y el
proyecto de Supabase se pausa tras 7 días sin actividad (los datos se conservan).
