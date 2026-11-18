# OsteoTraza · trazabilidad de muestras de defectos óseos

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

Aplicación web con menú lateral, buscador y usuarios por rol:

| Sección | Para qué |
|---|---|
| Inicio | Aviso **Cambiar EDTA**, ratones por paso y actividad reciente |
| Ratones | Ficha de cada ratón: paso actual, **linaje** (ratón → bloque → series → placas), placas, manejo, imagenología e historial |
| Placa | Etiqueta con rótulo y **código QR** (al escanearlo abre la ficha), ubicación, resultado e historial |
| Manejo | Ratones vivos y en decalcificación |
| Histología | Ratones agrupados por paso del procesamiento |
| Técnicas | Placas disponibles para IHQ/IF y resultados registrados |
| Ubicaciones | Árbol **lugar › contenedor › posición** con lo que hay en cada uno |

**Usuarios de prueba** (contraseña `demo123`): Javiera (histología), Docente responsable, Estudiante A, B y C.

| Rol | Registra |
|---|---|
| Histología | Inclusión/reinclusión, pares de desgaste, corte de set, tinción HE, archivo, ubicaciones, técnicas |
| Docente | Sacrificio, revisión SA, envío a histología |
| Estudiante | Cambios de EDTA, envío a histología, técnicas en placas (IHQ/IF u otra), ubicación de placas |

## Cómo ejecutarlo en local

Requiere Python 3.11 o superior.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 generar_datos.py              # crea data/prototipo.db con 30 ratones ficticios
uvicorn web.main:app --reload         # abre http://127.0.0.1:8000
```

Si existe `.streamlit/secrets.toml` (o `.env`) con `DATABASE_URL`, usa Supabase; si no, SQLite local.
La barra lateral indica qué base se está usando.

## Archivos

| Archivo | Función |
|---|---|
| `web/main.py` | Servidor web (FastAPI): recibe pedidos, llama a `servicios.py` y muestra páginas. |
| `web/templates/` | Páginas HTML. |
| `web/static/estilo.css` | Diseño propio. |
| `servicios.py` | Capa de lógica: único archivo que lee/escribe la base y aplica los permisos por rol. |
| `esquema.sql` | Tablas de la base de datos. |
| `generar_datos.py` | Genera los datos ficticios según las reglas del laboratorio. |
| `subir_a_supabase.py` | Copia la base local a PostgreSQL en Supabase. |
| `render.yaml` | Configuración para publicar en Render. |
| `docs/` | Problema, decisiones de arquitectura y sus razones. |
| `CLAUDE.md` | Reglas para el asistente de IA usado en el desarrollo. |

## Publicar (costo cero)

- **Base de datos:** Supabase (PostgreSQL). Crear `.streamlit/secrets.toml` con la línea
  `DATABASE_URL = "..."` (conexión *Session pooler*) y correr `python3 subir_a_supabase.py`.
- **App:** Render (plan gratuito, sin tarjeta). *New → Blueprint* → elegir el repositorio (usa `render.yaml`)
  → pegar `DATABASE_URL` cuando lo pida.

Notas del plan gratuito: la app se apaga tras 15 minutos sin uso y tarda ~1 minuto en despertar;
Supabase pausa el proyecto tras 7 días sin actividad (los datos se conservan).

## Decisiones principales

- **Capas separadas:** páginas (`web/`) / lógica y permisos (`servicios.py`) / base de datos. Gracias a esto
  se pudo cambiar de Streamlit a una web propia sin rehacer la lógica.
- **Base relacional** (ratón → bloque → placa → resultado). SQLite en desarrollo; PostgreSQL al publicar.
- **Costo cero:** Supabase + Render, sin tarjeta.
- **Trazabilidad:** cada acción queda como evento (quién, qué, cuándo).
