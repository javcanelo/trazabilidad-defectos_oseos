# Arquitectura del prototipo

Propuesta de la IA, revisada por Javiera. En cada decisión: completar "Mi decisión y razón".

## Requisitos
- Web publicada, usable desde el celular.
- Usuarios: responsable de histología, docente y estudiantes; todos escriben, cada uno su parte.
- ~30 sujetos procesados (habrá más). Datos ficticios (investigación no publicada).
- Imágenes: histología (HE) y microCT (Bruker/CTvox; reconstrucciones pesadas).

---------------------------------------------------------------------------
## DECISIONES

### D1. ¿Cómo se separan interfaz y lógica?
Clase: Natalia insistió en tener una capa intermedia (back/API) que valide y proteja los datos
(ej.: "solo un administrador puede borrar"), y criticó el "todo en uno".
- A) Streamlit "todo en uno": rápido, pero la lógica queda mezclada con la pantalla.
- B) Streamlit (pantalla) + módulo de lógica separado (`servicios.py`) que es el único que toca la
  base de datos y aplica las reglas de rol. Mismo esfuerzo que A, respeta la idea de la clase.
- C) Front + API real (FastAPI): lo más correcto, pero demasiado para una semana.
- Propuesta IA: **B**.
- Mi decisión y razón: B, aplico la separación sin construir una API completa porque no se alcanza en 1 semana.

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
| **Streamlit Community Cloud + Supabase (plan gratis)** | $0, sin tarjeta | Se conecta a GitHub; Supabase es PostgreSQL serverless e incluye almacenamiento de archivos | La app "duerme" tras 12 h sin uso (despierta al entrar); Supabase pausa el proyecto tras 7 días sin actividad (los datos se conservan); 500 MB de base y 1 GB de archivos |
- Desarrollo: SQLite en mi computador. Publicación: Streamlit Community Cloud + Supabase.
- Mi decisión y razón: Streamlit Community Cloud + Supabase, porque es el único camino serverless
  sin costo ni tarjeta. Descarté Cloud Run (sugerido en clase) porque exige tarjeta y quiero
  costo cero; descarté el notebook porque los usuarios no podrían entrar desde fuera de la red.
  Las limitaciones (pausas, cupos) son aceptables para un prototipo de ~30 sujetos.

### D5. ¿Dónde van las imágenes?
- Las imágenes NO van dentro de la base de datos; la base guarda solo su enlace (práctica estándar).
- HE: JPG comprimido. MicroCT: vista previa PNG (captura CTvox) en Supabase Storage (1 GB gratis).
- Reconstrucción original de microCT (muy pesada): enlace a su ubicación (ej. Drive institucional),
  no se sube al prototipo. Visor 3D: fuera del MVP.
- Mi decisión y razón: práctica estándar; separar archivos pesados de los datos mantiene la base
  liviana y respeta el cupo gratuito.

### D6. Seguridad mínima (requisitos no funcionales, vistos en clase)
- Login y 3 roles fijos (control de acceso por rol).
- Tabla de eventos: quién hizo qué y cuándo (trazabilidad).
- Contraseña de la base de datos en los "secrets" de Streamlit Cloud, nunca en el código ni en GitHub.
- Doble factor en las cuentas de GitHub, Streamlit y Supabase.
- Mi decisión y razón: se incluyen todos, porque según la clase son responsabilidades que no se
  delegan aunque sea un prototipo.

### D7. Interoperabilidad
Clase: no modelar la base con HL7/FHIR; si se necesita, una capa aparte que traduzca.
- Propuesta IA: modelo propio, interoperabilidad fuera del MVP (mencionar como trabajo futuro).
- Mi decisión y razón: de acuerdo; modelo propio según las necesidades del laboratorio y una
  capa de traducción solo si en el futuro hay que intercambiar datos.

---------------------------------------------------------------------------
## Roles (MVP: fijos)
| Rol | Registra | Ve |
|---|---|---|
| Histología (Javiera) | Bloques, placas, rótulos, técnica asignada | Todo |
| Docente | Sujetos, condición experimental, microCT | Todo |
| Estudiante | Tratamiento previo (ej. descalcificación EDTA) y resultado de su técnica en una placa, con comentario | Todo |

## Rótulo de la placa
Esmerilado del portaobjeto (~25 × 20 mm en un portaobjeto de 75 × 25 mm):
```
┌──────────────┐
│    NÚMERO    │   número del sujeto
│    TÉCNICA   │
│    FECHA     │
│ 07           │   correlativo de placa (esquina inferior izquierda)
└──────────────┘
```
- El correlativo es independiente de la técnica.
- Serie de desgaste: correlativo propio. Al pasar a sets de corte, el correlativo vuelve a 1.
- Tipo de portaobjeto: normal o cargado (para IHQ).
- El rótulo se muestra como texto; dibujar la placa queda fuera del MVP.

## Modelo de datos
- **sujeto**: id, caja, sexo, fecha_nacimiento, fecha_sacrificio, contenido_defecto (ej. células 200.000),
  tiempo_experimentacion, anestesia, experimento, grupo (control / experimental), lista (texto libre),
  tesis_responsable, ct_texto (texto libre), comentarios (texto libre)
- **procesamiento_previo**: id, sujeto_id, tipo (desmineralización / inclusión previa / otro), fecha, lugar, usuario
- **estudio_imagen**: id, sujeto_id, tipo (microCT), lugar (ej. Católica), fecha, vista_previa, archivo_original
- **bloque**: id, sujeto_id, fecha_reinclusion, estado (en lab / agotado / entregado)
- **placa**: id, bloque_id, serie (desgaste / set), correlativo, tipo_portaobjeto (normal / cargado),
  protocolo, tecnica, rotulo, estado (disponible / en técnica / terminada / descartada)
- **resultado_placa**: id, placa_id, usuario_id, tecnica_realizada (ej. IF + marcador), estado_final, comentario, fecha
- **imagen_placa**: id, placa_id, archivo, descripcion
- **usuario**: id, nombre, rol
- **evento**: id, usuario_id, entidad, entidad_id, accion, fecha, detalle  ← trazabilidad

## Pantallas (rediseñadas tras probar la etapa 2)
Menú principal con 4 tarjetas; casi todo vive dentro de la ficha del ratón.
- 🐭 **Ratones** → ficha: paso actual, último trabajo, dónde está el taco, línea del flujo y pestañas
  Placas (tira de recuadros por serie; al tocar una se ve rótulo, ubicación, resultado e historial),
  Manejo, Imagenología, Datos, Historial.
- 🧫 **Manejo**: vivos en experimentación y en decalcificación; aviso "Cambiar EDTA" si pasan
  3 o más días sin cambio (también aparece al abrir la app).
- 🔬 **Histología**: ratones agrupados por paso (recepción, reinclusión, desgaste, esperando SA,
  corte de set, tinción HE, placas en técnicas, archivado).
- 🧪 **Técnicas**: placas disponibles para IHQ/IF y resultados registrados.

## Etapas (UNA a la vez)
1. Datos ficticios (30 sujetos) + SQLite local.
2. Pantallas 2–4 (solo consulta), local.
3. Pantallas 1, 5 y 6 (login, escritura, historial).
4. Supabase (PostgreSQL + archivos) + publicar en Streamlit Community Cloud.
5. (Opcional) permisos a medida, visor 3D, capa de interoperabilidad.

## Criterio sobre la tabla de la docente
- Las columnas varían entre ratones (12 a 15 filas). Las de significado incierto (ej. "Lista", "CT")
  se guardan como texto libre, sin interpretarlas. Se agregan grupo (control/experimental) y comentarios.
