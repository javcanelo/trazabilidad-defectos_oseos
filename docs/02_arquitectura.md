# Arquitectura del prototipo (OsteoTraza)

Propuesta de la IA, revisada y decidida por Javiera. Cada decisión tiene su razón.

## Requisitos
- Web publicada, usable desde el celular.
- Usuarios: docente, TM de histología, estudiantes y un administrador; cada uno registra su parte.
- 15 sujetos ficticios en la demo (en el estudio real son ~30 y habrá más).
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
  (pausas, cupos) son aceptables para un prototipo.

### D5. ¿Dónde van las imágenes?
- Las imágenes NO van dentro de la base de datos; la base guarda solo su enlace (práctica estándar).
- HE: JPG comprimido. MicroCT: vista previa PNG (captura CTvox).
- Reconstrucción original de microCT (muy pesada): enlace a su ubicación (ej. Drive institucional),
  no se sube al prototipo. Visor 3D: fuera del MVP.
- Estado: la pestaña Imagenología muestra una vista previa de microCT de ejemplo (la misma para
  todos los ratones), guardada en `web/static/` y excluida de GitHub con `.gitignore`. Subir
  imágenes propias (Supabase Storage, 1 GB gratis) queda como trabajo futuro.
- Mi decisión y razón: práctica estándar; separar archivos pesados de los datos mantiene la base
  liviana y respeta el cupo gratuito.

### D6. Seguridad mínima (requisitos no funcionales, vistos en clase)
- Login y 4 roles (Docente, TM, Estudiante, Admin), validados en `servicios.py`, no en la pantalla.
- Contraseñas de usuarios guardadas cifradas, nunca en texto plano.
- Tabla de eventos: quién hizo qué y cuándo (trazabilidad).
- Contraseña de la base de datos fuera del código y de GitHub: en un archivo de secretos local
  (excluido por `.gitignore`) y como variable de entorno en Render.
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
- Web propia (FastAPI + HTML/CSS): diseño libre tipo software de laboratorio (menú lateral, fichas, linaje).
- Decisión: **web propia**. Se reutilizan `servicios.py` y la base de datos, porque las capas
  estaban separadas (D1). Publicación: **Render** (gratis, sin tarjeta) + Supabase.
- Mi razón: quería otro aspecto y Streamlit limitaba el diseño. Como la lógica y la base estaban
  separadas (D1), solo cambié la interfaz.

### D9. Ajustes después de probar el flujo completo (decidido tras la etapa 5)
Probé la app paso a paso con cada rol y anoté qué no calzaba con cómo se trabaja de verdad.
- **Ubicación solo por laboratorio** (Bioterio, Lab. A, Lab. B), no por gaveta, caja y posición:
  el detalle era ruido. La muestra se queda donde está salvo que alguien la mueva, y se puede
  mover sin cambiar de etapa, una por una o varias a la vez.
- **Sin códigos QR**: el QR solo abría la ficha que ya estaba abierta en pantalla. Tendría sentido
  si sirviera para registrar un paso escaneando; queda como trabajo futuro.
- **Roles según cómo se trabaja hoy** (ver tabla). La TM no hace manejo; la docente puede revisar,
  cambiar EDTA y registrar técnicas.
- **Fijación en formalina** como paso propio: después del sacrificio no se entra directo a EDTA.
- **Desgaste en dos pasos**: primero se registra cuántas placas se cortaron y después, cuando se
  tiñe, cuáles se tiñeron. Recién ahí pasa a revisión.
- **La revisión no archiva**: decide entre profundizar desgaste o indicar set. Archivar es
  consecuencia de terminar el set.
- **Placa inutilizable** (rota, perdida, desprendida) en vez de "perdida": queda el registro, pero
  ya no se le puede hacer nada.
- **Registro por lote** de inclusión y tinción HE desde Histología.
- **Avisos por rol**: cambio de EDTA (docente, estudiantes), revisión pendiente (docente) y set
  indicado sin cortar (TM).
- Mi razón: el prototipo tiene que parecerse al trabajo real; si no, nadie lo usaría.

---------------------------------------------------------------------------
## Roles
Todos ven todo; cada rol registra solo lo suyo (según cómo se trabaja hoy).

| Registra | Docente | TM (Javiera) | Estudiante | Admin |
|---|---|---|---|---|
| Ingresar y editar ratones | Sí | No | No | Sí |
| Sacrificio y fijación en formalina | Sí | No | No | Sí |
| Inicio de decalcificación y cambios de EDTA | Sí | No | Sí | Sí |
| Envío a histología | No | No | Sí | Sí |
| Pasos de histología (inclusión, desgaste, set, HE, archivo) | No | Sí | No | Sí |
| Revisión (profundizar desgaste o indicar set) | Sí | Sí | No | Sí |
| Técnicas en placas e inutilizable | Sí | Sí | Sí | Sí |
| Mover muestras de laboratorio | Sí | Sí | Sí | Sí |

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
- Serie de desgaste: se registran las placas cortadas y luego las que se tiñen con HE; revisión tras cada ronda.
- Al pasar a sets de corte (estándar, estrella, corazón), el correlativo vuelve a 1.
- Tipo de portaobjeto: normal (HE) o cargado (IHQ/IF).

## Modelo de datos
- **usuario**: id, nombre, rol (docente / tm / estudiante / admin), clave_hash
- **sujeto**: id, caja, sexo, fecha_nacimiento, fecha_cirugia, fecha_sacrificio, contenido_defecto_izq,
  contenido_defecto_der, tiempo_experimentacion, anestesia, experimento, grupo (control / experimental),
  lista (texto libre), tesis_responsable, ct_texto (texto libre), comentarios (otros datos libres)
- **decalcificacion**: id, sujeto_id, fecha_inicio, fecha_fin (vacía = en curso; sin fila = en formalina)
- **cambio_edta**: id, sujeto_id, fecha, usuario_id
- **procesamiento_previo**: id, sujeto_id, tipo, fecha, lugar, usuario_id
- **estudio_imagen**: id, sujeto_id, tipo (microCT), lugar, fecha, vista_previa, archivo_original
- **bloque**: id, sujeto_id, forma_llegada (cubo de parafina / cabeza en EDTA), fecha_recepcion,
  fecha_reinclusion, paso, estado, ubicacion (laboratorio)
- **placa**: id, bloque_id, serie (desgaste / set), correlativo, tipo_portaobjeto, protocolo, destino,
  tecnica, fecha_corte, fecha_tecnica, rotulo, ubicacion (laboratorio),
  estado (disponible / en técnica / terminada / inutilizable)
- **resultado_placa**: id, placa_id, usuario_id, tecnica_realizada, estado_final (realizada / con
  observaciones / en proceso / repetir / inutilizable), comentario, fecha
- **imagen_placa**: id, placa_id, archivo, descripcion
- **evento**: id, usuario_id, entidad, entidad_id, accion, fecha, detalle  ← trazabilidad

## Pasos del flujo
Manejo: En experimentación → Fijación en formalina → Decalcificación (EDTA).
Histología: Recepción / Reinclusión → Desgaste → Esperando revisión → (Desgaste otra vez o)
Corte de set → Tinción HE → Placas en técnicas → Archivado.

## Pantallas (versión final, web propia)
- **Inicio**: lo que le toca a cada rol (avisos de EDTA, revisiones y sets sin cortar), actividad
  reciente y ratones por paso.
- **Ratones**: lista que se puede ordenar y filtrar; botón para ingresar ratones. Ficha: paso y
  laboratorio arriba, formulario según rol y paso, pestañas Linaje, Placas, Manejo, Imagenología, Historial.
- **Placa**: etiqueta con rótulo, registrar técnica, marcar inutilizable, mover.
- **Manejo**: vivos, en formalina y en decalcificación.
- **Histología**: ratones agrupados por paso, con registro por lote.
- **Técnicas**: placas disponibles para IHQ/IF y resultados filtrables.
- **Ubicaciones**: Bioterio, Lab. A y Lab. B con su contenido; mover varias muestras a la vez.
- **Buscador**: por número de ratón o rótulo.

## Etapas (una a la vez)
1. Datos ficticios + SQLite local.
2. Pantallas de consulta (Streamlit). Rediseñadas tras probarlas: menú y ficha centrada en el ratón.
3. Login, permisos por rol, registro de acciones e historial automático.
4. Supabase (PostgreSQL) + publicación.
5. Web propia (FastAPI): diseño tipo LIMS y linaje; publicación en Render.
6. Pruebas del flujo completo con cada rol y ajustes (D9).
7. Trabajo futuro: carga de imágenes, QR para registrar pasos, campos a medida, permisos editables,
   visor 3D, capa de interoperabilidad, contraseñas individuales.

## Criterio sobre la tabla de la docente
- Las columnas varían entre ratones (12 a 15 filas). Las de significado incierto (ej. "Lista", "CT")
  se guardan como texto libre, sin interpretarlas. Se agregan grupo (control/experimental) y comentarios.
- En la ficha solo se muestran los datos que se usan (sexo, defectos, fechas). Lo demás (tesis,
  experimento, etc.) se puede agregar como "otros datos" libres al ingresar o editar un ratón.
