# Cuaderno de aprendizaje

## 0. Punto de partida
- No partí de cero: tenía un proyecto anterior simple para seguir las muestras de este mismo estudio.
  Guardaba los datos en un archivo JSON, se actualizaba desde Streamlit en mi computador y se publicaba
  como una página de solo consulta. Registraba la etapa de cada muestra, un historial y los protocolos de corte.
- Lo que mejoró en este prototipo:
  - Pasé de seguir la muestra a seguir cada placa (técnica, rótulo, ubicación y resultado).
  - Base de datos relacional en vez de un archivo JSON.
  - Varios usuarios con roles que registran su parte, no solo consulta.
  - Publicado en la nube y usable desde el celular.
  - Manejo y aviso de cambio de EDTA, linaje, ubicaciones jerárquicas y etiquetas con QR.

## 1. Partir por el problema, no por la solución
- Lo primero fue escribir el problema en un párrafo, sin lenguaje técnico, antes de pedir código.
- Cuando expliqué mal el flujo, la IA construyó algo que no servía: la primera versión de las pantallas
  estaba organizada según la base de datos y no según cómo se trabaja en el laboratorio. Al explicar el flujo
  real (llegada en cubo o en EDTA, desgaste en pares, revisión SA, sets de corte, técnicas), el diseño mejoró.
- Aprendizaje: como dijo la profesora, muchos errores de la IA vienen de un problema mal explicado.
  El conocimiento clínico/técnico es lo que define qué se construye.

## 2. Frenar a la IA y avanzar por etapas
- Usé un archivo `CLAUDE.md` con reglas: preguntar antes de ejecutar, una etapa a la vez, explicar el porqué,
  nunca datos reales.
- Trabajé en etapas: datos ficticios → pantallas de consulta → login y registro → nube → web propia.
- Aprendizaje: avanzar de a poco permitió corregir el rumbo temprano (por ejemplo, rediseñar las pantallas
  después de probarlas).

## 3. Datos ficticios
- Aunque son ratones y no hay restricción legal, la investigación no está publicada, así que usé solo datos
  inventados con las reglas reales del laboratorio.
- Los datos inventados también tienen que tener sentido: tuve que corregir la serie de desgaste, los dos
  defectos por ratón, el formato del rótulo (dd/mm/aa) y cuándo nace el rótulo (al hacer la técnica).

## 4. Base de datos relacional
- Una base relacional son tablas unidas entre sí: cada placa apunta a su bloque y cada bloque a su ratón.
- Esto permite preguntar cosas como "¿qué placas de este ratón quedan disponibles para IHQ?".
- Usé SQLite (un archivo) para desarrollar y PostgreSQL (Supabase) para publicar; el mismo código funciona con ambas.

## 5. Capas separadas (lo más importante que aprendí)
- `servicios.py` es la capa intermedia: es el único archivo que lee y escribe la base y aplica las reglas de
  quién puede hacer qué. Las pantallas solo muestran y piden.
- Los permisos van en la capa intermedia y no en la pantalla, porque ocultar un botón no impide que alguien
  haga la acción por otro camino. La regla se valida donde están los datos.
- Esta separación permitió cambiar toda la interfaz (de Streamlit a una web propia) sin rehacer la lógica ni la base.

## 6. Trazabilidad
- Cada acción queda como evento: quién, qué, cuándo, sobre qué ratón/bloque/placa.
- Cada placa tiene ubicación (lugar › contenedor › posición), rótulo y código QR que abre su ficha.
- Equivalente clínico: saber en todo momento dónde está una muestra de biopsia y qué se le hizo.

## 7. Infraestructura y costos
- Opciones vistas en clase: computador propio, servidor arrendado, nube administrada y serverless.
- Elegí serverless gratuito y sin tarjeta: Supabase (base de datos) y Render (app). Descarté Cloud Run porque pide tarjeta.
- Limitaciones aceptadas: la app se apaga tras 15 min sin uso y Supabase pausa el proyecto tras 7 días
  sin actividad. Me pasó: el proyecto se pausó y tuve que restaurarlo.

## 8. Seguridad básica
- La contraseña de la base nunca va en el código ni en GitHub: va en un archivo de secretos excluido por
  `.gitignore` y en las variables de entorno de Render.
- Las contraseñas de los usuarios se guardan cifradas.
- Problemas reales que resolví: una contraseña con símbolos rompía la URL de conexión, y tuve que usar la
  conexión "Session pooler" de Supabase.

## 9. Herramientas que aprendí a usar
- Entorno virtual (`.venv`): instalar librerías solo para el proyecto.
- Git: `git add`, `commit`, `push`; `git status` para revisar antes de subir; Git guarda solo lo que cambió.
- Carpetas ocultas (las que empiezan con punto) no se ven con `ls`, sí con `ls -a`.
- Leer errores: muchos dicen exactamente qué falta (por ejemplo, una librería no instalada).

## 10. Cambiar de opinión con argumentos
- Primero elegí Streamlit (rápido). Al verla funcionando no me gustó el diseño, y cambié a una web propia
  con estilo de software de laboratorio. El cambio fue posible gracias a las capas separadas.

## 11. Transferencia a pacientes
- Equivalencias: ratón ≈ paciente; condición experimental ≈ diagnóstico o tratamiento; microCT ≈ TC; bloque y placas ≈ biopsia en anatomía patológica; IHQ/IF ≈ técnicas complementarias; historial ≈ trazabilidad de la muestra.
- Lo que más se transfiere es el registro temporal y de ubicación: en patología, perder una biopsia es un evento centinela, y un error de fecha (por ejemplo en fijación o decalcificación) puede arruinar una muestra. El mismo modelo serviría para un servicio de anatomía patológica o para el manejo de muestras en ensayos clínicos.

## 12. Trabajo futuro
- Subir imágenes (HE y vista previa de microCT).
- Contraseñas individuales y permisos a medida.
- Capa de interoperabilidad si hay que intercambiar datos con otros sistemas.
- Cargar los datos reales si el laboratorio lo aprueba, en una versión privada.