# Arquitectura del prototipo (OsteoTraza)

Propuesta de la IA, revisada y decidida por Javiera. Cada decisión tiene su razón.

## Requisitos
- Web publicada, usable desde el celular.
- Usuarios: responsable de histología, docente y estudiantes; todos escriben, cada uno su parte.
- ~30 sujetos procesados (habrá más). Datos ficticios (investigación no publicada).
- Imágenes: histología (HE) y microCT (Bruker/CTvox; reconstrucciones pesadas).
- Costo cero, sin tarjeta de crédito.

---------------------------------------------------------------------------
## DECISIONES

### D1. ¿Cómo se separan interfaz y lógica?
Clase: Natalia insistió en tener una capa intermedia (back/API) que valide y proteja los datos
(ej.: "solo un administrador puede borrar"), y criticó el "todo en uno".
- A) Streamlit "todo en uno": rápido, pero la lógica queda mezclada con la pantalla.
- B) Streamlit (pantalla) + módulo de lógica separado (`servicios.py`) que es el único que toca la
  base de datos y aplica las reglas de rol.
- C) Front + API real (FastAPI): lo más correcto, pero parecía demasiado para una semana.
- Mi decisión y razón: B, aplico la separación sin construir una API completa porque no se alcanza en 1 semana.
- Resultado posterior: esta separación permitió pasar a la opción C (ver D8) sin rehacer la lógica.

### D2. ¿Base de datos relacional o no relacional?
Clase: Firebase es no relacional; Natalia advirtió no elegir tecnologías complejas por atractivas
(en Japón una base no relacional falló con consultas complejas).
- A) Relacional (PostgreSQL / SQLite): calza con la cadena sujeto → bloque → placa → resultado y
  facilita cruzar datos. Contra: hay que definir las tablas desde el inicio.
- B) No relacional (Firestore/Firebase): flexible, pero cruzar información es difícil.
- Mi decisión y razón: A, por la naturaleza del flujo (cada placa pertenece a un bloque y cada
  bloque a un sujeto). El contra es aceptable porque el flujo ya lo conozco bien.

### D3 + D4. ¿Dónde viven la app y la base de datos? (restricción: COSTO CERO, sin tarjeta)
Clase: 4 opciones (computador propio, servidor arrendado, nube administrada, serverless).
| Opción | Costo | A favor | En contra |
|---|---|---|---|
| Notebook propio siempre prendido | $0 | Control total | Según la clase, desde fuera de la red no se puede suponer acceso; depende de que el equipo no se apague |
| Google Cloud Run + Cloud SQL | Pide tarjeta; Cloud SQL se paga | Lo sugirió la docente; serverless | Riesgo de cobro; no cumple costo cero |
| Streamlit Community Cloud + Supabase | $0, sin tarjeta | Se conecta a GitHub; Supabase es PostgreSQL serverless | Solo sirve para apps hechas en Streamlit |
| **Render + Supabase (plan gratis)** | $0, sin tarjeta | Publica cualquier app Python desde GitHub | La app se apaga tras 15 min sin uso (~1 min en despertar); Supabase pausa el proyecto tras 7 días sin actividad (los datos se conservan) |
- Desarrollo: SQLite en mi computador. Publicación: Supabase (base) + Render (app).
- Mi decisión y razón: Supabase para la base, porque es PostgreSQL serverless sin costo ni tarjeta.
  Descarté Cloud Run (sugerido en clase) porque exige tarjeta y quiero costo cero; descarté el
  notebook porque los usuarios no podrían entrar desde fuera de la red. Primero publiqué en
  Streamlit Community Cloud y luego pasé a Render al dejar Streamlit (D8). Las limitaciones
  (pausas, cupos) son aceptables para un prototipo de ~30 sujetos.

### D5. ¿Dónde van las imágenes?
- Las imágenes NO van dentro de la base de datos; la base guarda solo su enlace (práctica estándar).
- HE: JPG comprimido. MicroCT: vista previa PNG (captura CTvox) en Supabase Storage (1 GB gratis).
- Reconstrucción original de microCT (muy pesada): enlace a su ubicación (ej. Drive institucional),
  no se sube al prototipo. Visor 3D: fuera del MVP.
- Estado: el modelo de datos ya tiene los campos; la carga de imágenes queda como trabajo futuro.
- Mi decisión y razón: práctica estándar; separar archivos pesados de los datos mantiene la base
  liviana y respeta el cupo gratuito.

### D6. Seguridad mínima (requisitos no funcionales, vistos en clase)
- Login y 3 roles fijos (control de acceso por rol), validados en `servicios.py`, no en la pantalla.
- Contraseñas de usuarios guardadas cifradas, nunca en texto plano.
- Tabla de eventos: quién hizo qué y cuándo (trazabilidad).
- Contraseña de la base de datos fuera del código y de GitHub: en `.streamlit/secrets.toml` (local,
  excluido por `.gitignore`) y como variable de entorno en Render.
- Doble factor en las cuentas de GitHub, Render y Supabase.
- Pendiente para una versión real: la contraseña de prueba (`demo123`) es pública y compartida.
- Mi decisión y razón: se incluyen todos, porque según la clase son responsabilidades que no se
  delegan aunque sea un prototipo.

### D7. Interoperabilidad
Clase: no modelar la base con HL7/FHIR; si se necesita, una capa aparte que traduzca.
- Propuesta IA: modelo propio, interoperabilidad fuera del MVP (mencionar como trabajo futuro).
- Mi decisión y razón: de acuerdo; modelo propio según las necesidades del laboratorio y una
  capa de traducción solo si en el futuro hay que intercambiar datos.

### D8. ¿Seguir con Streamlit o hacer una web propia? (decidido tras la etapa 4)
- Streamlit: rápido, pero el diseño queda limitado ("se ve a Streamlit") y no lo imaginé así.
- Web propia (FastAPI + HTML/CSS): diseño libre tipo software de laboratorio (menú lateral, fichas,
  linaje, etiquetas con QR, ubicaciones jerárquicas).
- Decisión: **web propia**. Se reutilizan sin cambios `servicios.py` y la base de datos, porque las
  capas estaban separadas (D1). Publicación: **Render** (gratis, sin tarjeta) + Supabase.
- Mi razón: (completar)

---------------------------------------------------------------------------
## Roles
| Rol | Registra | Ve |
|---|---|---|
| Histología (Javiera) | Inclusión/reinclusión, pares de desgaste, corte de set, tinción HE, archivo, ubicaciones, técnicas | Todo |
| Docente | Sacrificio (inicia decalcificación), revisión SA, envío a histología | Todo |
| Estudiante | Cambios de EDTA, envío a histología, técnica en una placa (IHQ/IF u otra) con resultado y comentario, ubicación de placas | Todo |

## Rótulo de la placa
Esmerilado del portaobjeto (~25 × 20 mm en un portaobjeto de 75 × 25 mm):
```
┌──────────────┐
│    NÚMERO    │   número del sujeto
│    TÉCNICA   │   (+ detalle, ej. marcador)
│   dd/mm/aa   │
│ 7            │   correlativo de placa (esquina inferior izquierda)
└──────────────┘
```
- El rótulo nace cuando se hace la técnica, no al cortar.
- El correlativo es independiente de la técnica.
- Serie de desgaste: pares; se tiñe con HE la placa par; revisión SA tras cada ronda.
- Al pasar a sets de corte (estándar, estrella, corazón), el correlativo vuelve a 1.
- Tipo de portaobjeto: normal (HE) o cargado (IHQ/IF).
- La ficha de cada placa muestra su etiqueta con un código QR que abre la ficha desde el celular.

## Modelo de datos
- **usuario**: id, nombre, rol, clave_hash
- **sujeto**: id, caja, sexo, fecha_nacimiento, fecha_cirugia, fecha_sacrificio, contenido_defecto_izq,
  contenido_defecto_der, tiempo_experimentacion, anestesia, experimento, grupo (control / experimental),
  lista (texto libre), tesis_responsable, ct_texto (texto libre), comentarios
- **decalcificacion**: id, sujeto_id, fecha_inicio, fecha_fin (vacía = en curso)
- **cambio_edta**: id, sujeto_id, fecha, usuario_id
- **procesamiento_previo**: id, sujeto_id, tipo, fecha, lugar, usuario_id
- **estudio_imagen**: id, sujeto_id, tipo (microCT), lugar, fecha, vista_previa, archivo_original
- **bloque**: id, sujeto_id, forma_llegada (cubo de parafina / cabeza en EDTA), fecha_recepcion,
  fecha_reinclusion, paso, estado, ubicacion
- **placa**: id, bloque_id, serie (desgaste / set), correlativo, tipo_portaobjeto, protocolo, destino,
  tecnica, fecha_corte, fecha_tecnica, rotulo, ubicacion, estado (disponible / en técnica / terminada / perdida)
- **resultado_placa**: id, placa_id, usuario_id, tecnica_realizada, estado_final (realizada / con
  observaciones / en proceso / repetir / perdida), comentario, fecha
- **imagen_placa**: id, placa_id, archivo, descripcion
- **evento**: id, usuario_id, entidad, entidad_id, accion, fecha, detalle  ← trazabilidad

Ubicaciones jerárquicas como ruta: `Lugar › Contenedor › Posición`
(ej. `Gaveta de placas A › Caja 2 › Pos 14`). Al cortar, la posición se asigna automáticamente.

## Pantallas (versión final, web propia)
- **Inicio**: aviso "Cambiar EDTA" (3+ días sin cambio) con botón "Cambié EDTA hoy", ratones por paso
  y actividad reciente.
- **Ratones** → ficha: paso actual (antes → ahora → sigue), formulario según rol y paso, panel de
  propiedades (dónde está, resumen, datos) y pestañas Linaje, Placas, Manejo, Imagenología, Historial.
- **Placa**: etiqueta con rótulo y QR, registrar técnica, mover, historial.
- **Manejo**: vivos y en decalcificación.
- **Histología**: ratones agrupados por paso.
- **Técnicas**: placas disponibles para IHQ/IF y resultados.
- **Ubicaciones**: árbol de lugares y contenedores con su contenido.
- **Buscador**: por número de ratón, rótulo o ubicación.

## Etapas (una a la vez)
1. Datos ficticios (30 sujetos) + SQLite local.
2. Pantallas de consulta (Streamlit). Rediseñadas tras probarlas: menú y ficha centrada en el ratón.
3. Login, permisos por rol, registro de acciones e historial automático.
4. Supabase (PostgreSQL) + publicación.
5. Web propia (FastAPI): diseño tipo LIMS, linaje, ubicaciones jerárquicas, etiquetas con QR; publicación en Render.
6. Trabajo futuro: carga de imágenes, permisos a medida, visor 3D, capa de interoperabilidad, contraseñas individuales.

## Criterio sobre la tabla de la docente
- Las columnas varían entre ratones (12 a 15 filas). Las de significado incierto (ej. "Lista", "CT")
  se guardan como texto libre, sin interpretarlas. Se agregan grupo (control/experimental) y comentarios.