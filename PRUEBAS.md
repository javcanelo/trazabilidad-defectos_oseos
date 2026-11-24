# Pruebas OsteoTraza

Antes de empezar: corre `python generar_datos.py` y `python subir_a_supabase.py` (escribe SI).
Clave de todos los usuarios: `demo123`. Usa la fecha de hoy salvo que se indique otra.

**Cómo comentar cada bloque** (una línea por punto basta):
- ✅ / ❌ ¿Funcionó?
- Si falló: qué hiciste, qué esperabas y qué pasó (copia el mensaje de error si salió).
- ¿Algo te confundió? (un botón que no encontraste, un nombre raro, un paso de más)
- ¿Falta algo que en el lab sí harías en este paso? (anótalo como mejora futura)

---

**A. Permisos por rol**

1. Entra como **Estudiante A** y abre el ratón `9746945` (En experimentación). No debería aparecer "Registrar sacrificio".
2. En el mismo ratón, entra como **Docente responsable**. No debería aparecer "Cambiar ubicación".

**Comentarios:**

1. para MVP/prototipo no es necesario ahora. no aparece.
2. sí aparece registrar sacrificio. no sale cambiar ubicacion.

---

**B. Manejo (Docente responsable)**

3. En el ratón `9746945`, registra el sacrificio. Debería pasar a Decalcificación, quedar en Bioterio y aparecer en **Manejo**.

**Comentarios:**

3. acá esta el problema de la formalina... hy que ponerlo porque no peude aparecer al tiro en edta, tiene qu ser sacrifico y que se paso  en formalina, es automatico, y leugo iniciar decalcifciaciom.
extra. problema viendo mas sobre ese raton, esto es todo lo que dice tipo al final Dónde está
Bioterio

Resumen
Último trabajo
Inicio decalcificación EDTA - 2026-11-24
Placas
0
HE teñidas
0
Datos
Sexo
Macho
Caja
3
Experimento
Defecto calvarial bilateral
Tesis
Tesis B
Lista
estándar
comentarios extra: el "dnode está" deeberia salir tipo al inciio ene stas partes Ratón 9746945
Decalcificación
control
izq.: vacío
der.: vacío, no tener que andar buscando al final en donde está porque es dato relevante. (no solo en qué está)
ultimo trabajoe sta ok, placas y he teñidas no esta tan bien porque es un ratonq  ni siquiera esta sacrificado, eso aparece recien cuano se desgasta que empiezas a gnerar placas...
en datos esta todo ok solo que caja exprimento tesis y lista no deberian ir, o sea lista no va proque eeso se lo asigna SA y y tesis peude q no este asociada a ningun  yexpriemtno es el mismo. podrian ir como extras pero meh. tipo cuando se ingresa un raton o edita un raton se le podrian meter campos de datos que quiera el usuario, algunos si o si van eso si.

---

**C. EDTA (Histología, Javiera)**

4. ⚠️ En **Manejo**, revisa que el ratón `9880593` tenga alerta (5 días sin cambio de EDTA). El `9611087` (1 día) no debería tenerla.
5. Registra el cambio de EDTA en `9880593`. Su alerta debería desaparecer.

**Comentarios:**

4. en efecto muestra alerta, y el otro de 1 dia no 
5. caundo abro el rato no me sale en nignun lugar ningun boton que em deje cambiar, solo registrar envio a histologia...  o sea hago click en manejo me meustra un 1 rojo luego me ice en rojo cambiar la 9880593 y hago click en el numero porque es lo unico clickeable y me cambia a la pestaña ratones y me meustra esto OsteoTraza
Inicio
Ratones
Manejo
1
Histología
Técnicas
Ubicaciones
D
Buscar ratón, rótulo o ubicación…
Ratones
9880593
Ratón 9880593
Decalcificación
control
izq.: vacío
der.: vacío

 Cambio de EDTA - 2026-11-19
Decalcificación
Envío a histología
 Registrar: Envío a histología
Cubo de parafina
Cabeza en EDTA
Fecha
24-11-2026
Registrar envío a histología
Linaje
Placas
(0)
Manejo
Imagenología
Historial
Ratón
Nacimiento
2026-05-24
Cirugía
2026-08-16
Defecto izquierdo
vacío
Defecto derecho
vacío
Experimentación
12 semanas
Anestesia
0,10 ml
Sacrificio / formalina
2026-11-08
Decalcificación EDTA
Inicio
2026-11-10
Fin
en curso
Cambios
3
Último cambio
hace 5 días toca cambiar
Cambios de EDTA
Fecha	Quién
2026-11-19	Estudiante B
2026-11-16	Estudiante B
2026-11-13	Estudiante B
Dónde está
Bioterio

Resumen
Último trabajo
Cambio de EDTA - 2026-11-19
Placas
0
HE teñidas
0
Cambiar EDTA
último cambio hace 5 días
Datos
Sexo
Macho
Caja
3
Experimento
Defecto calvarial bilateral
Tesis
Tesis B
Lista
corazón

---

**D. Flujo histológico completo (alternando roles)**

6. *Javiera:* en el ratón `9746945`, envíalo a histología como "cabeza en EDTA". Debería aparecer en Histología › Recepción y en Lab. Histología.
7. *Javiera:* registra la inclusión. Debería pasar a Desgaste.
8. *Javiera:* corta el par de desgaste. Revisa que **ya no te pida caja**, que se creen 2 placas y que pase a Esperando revisión SA.
9. *Docente:* en la revisión SA, elige "Indicar set de corte" con el protocolo "estrella". Debería pasar a Corte de set.
10. *Javiera:* corta el set. Revisa que no pida caja, que se creen las placas y que pase a Tinción HE.
11. *Javiera:* registra la tinción HE. Debería pasar a Placas en técnicas.

**Comentarios:**

extra: yo soy javiera, solo tengo rol en histologia y tecnicas, no previo. deberiamos cambiar los roles... tipo poner roles: Profesora, TM, Estudiante, ADMIN (que haga todo lo posible xd) que hagan sentido con sus funciones.
extra2: la lista de ratones en la pestaña ratones está ordenadda por numero correlativo, deberia idealmetne poder decidir como ordenarla.
extra3: en la parte de histologia no hay que poner esa columna dde HE y el numero... es irrelevante.
extra4: el 1 que mostraba manejo porque habia un raton sin cambiarle edta esta super bueno pero deberia mostrar mas de ese tipo en histologia tecnicas ratones ubicaicones, tipo si hace sentido que ahya alguna alerta, si no no incluyas. me puedes dar iddeas de qué alerta poner y te dijo SI o NO.
6. OK
7. ACA IDEALMENTE la inclusion y el desgaste a veces se hace de a 1 pero varias veces se hace de a batch,d eberia haber tipo posibiliades de ignresar asi tipo "registrar inclusiones" y registro bvarias no ir raton por raton. me molesta que siempre vaya a la pestaña ratones. aca la veia enr ecepcion y lo unico q me dejo clickear fue clusión en casete lo que hizo que se fuera desgaste.
8. acá no corto y tiño al mismo timpo xd corto y luego tiño cuando se me da la gana, y no siempre tiño laa 2 o la 1, tiene q darme a escoger cuantas palcas de desgaste saqué y cual luego voy a teñir.
9. clickeo en un ratonq ue esta para revision y no me deja seleccionarle el set OsteoTraza
Inicio
Ratones
Manejo
1
Histología
Técnicas
Ubicaciones
J
Buscar ratón, rótulo o ubicación…
Ratones
9177601
Ratón 9177601
Esperando revisión SA
experimental
izq.: andamio + células 200.000
der.: andamio + células 200.000

 Desgaste ronda 3: corte de par y HE - 2026-11-22
Esperando revisión SA
Profundizar desgaste o corte de set (según SA)
Linaje
Placas
(6)
Manejo
Imagenología
Historial
9177601
experimental, macho
Manejo
cirugía 2026-08-06, sacrificio 2026-10-01, 6 cambios de EDTA
microCT
2026-10-03
Bloque
9177601-B1
cubo de parafina, Lab. Histología
Desgaste (evaluación)
6 placas
1
2
3
4
5
6
HE
Normal sin teñir
Cargada disponible
Técnica realizada
En proceso
Repetir
No utilizable
Dónde está
Lab. Histología

Cambiar ubicación del bloque

Lab. Histología
Guardar
Resumen
Último trabajo
Desgaste ronda 3: corte de par y HE - 2026-11-22
Placas
6
HE teñidas
3
Llegó como
cubo de parafina
Recepción
2026-10-30
(Re)inclusión
2026-11-03
Datos
Sexo
Macho
Caja
3
Experimento
Defecto calvarial bilateral
Tesis
Tesis A
Lista
—
10. OK
11. OK

---

**E. Técnicas (Estudiante B)**

12. En **Técnicas**, abre una placa cargada del ratón `9746945`.
13. Registra la técnica: IHQ/IF, marcador "CD31", resultado "realizada", laboratorio Lab. Anatomía Patológica.
14. Revisa que la placa diga Lab. Anatomía Patológica y que el historial muestre "Estudiante B".
15. ⚠️ En otra placa, registra una técnica con resultado **"no utilizable"**. La placa debería quedar con ese estado y **seguir en su laboratorio**.

**Comentarios:**

extra: no es relevante qué set s en placas disponibles.
extra2: posiblidad de ordenar/filtrar la lista de resultados registrados.
12. aparece el QR, ese QR por q aparece? xd es solo relevante en esta etapa? la idea era tipo que se peudan ingresar con QR no que el QR sirva para ver los datos porque el QR se ve desde la misma pestaña que peudes hacer click para ver el etalle del raton xddddd no tiene snetido. la idea podria funcionar si tipo por raton peudes generar un qr que luego puedas por ejemplo no se, si quiero ingresar algo de tal raton solo leo el QR y me redigide de inmediato al raton pero no le veo mas utilidad. la idea de un qr era que ayduara a registrar los pasos sin necesidad de que alguien abra el link, la pagina, busque el raton, y etc. si noe s implementable lo sacamos.
13. no es reelvante mostrar dónde queda la placa, se asume que queda en donde partio (por eso es relevante poder modificar la localizacion de las coaas porque peuden haber cambios e mano tipo yo tengo toda slas palcas vacias y leugo me las vienen a pedir y se van a otro lab, no pasó ningun paso pero tengo q registrar que se movieron. tambien tipo por batch.)
14. no es relevant el historial de l aplaca porque no puedes hacerle una tecnica adicional a la misma placa xd. lo unico relevante es ver capaz cuáno se hizo la tecnica y si se movió de lugar pero mas q eso nada, es exceso de informacion.
15. si está inutilizable ( no es "no utilziable" e s"inutilizable") no deberia dejar poner que marcador xd si no se le va a hacer anda ni tampoco marcar donde stá,d eberia en realiddad poder ponerle tipo solo inutilizable y que la weadeje de exister, o sea está el registro pero no peudes hacer nada con ella es un simil a botarla a la basura.

---

**F. Ubicaciones**

16. ⚠️ En **Ubicaciones** deberías ver solo **Lab. Histología** y **Lab. Anatomía Patológica**, con sus conteos.
17. ⚠️ Haz clic en Lab. Anatomía Patológica. Deberían aparecer tus placas de los pasos 13 y 15, además de las que ya estaban.
18. *Javiera:* en una placa, usa "Mover placa" para llevarla a Lab. Histología. El conteo debería cambiar.

**Comentarios:**

16. sí, falta en bioterio cuantos ratones hay...
17. esto sale en lab anatomia paotlgia OsteoTraza
Inicio
Ratones
Manejo
Histología
Técnicas
Ubicaciones
E
Buscar ratón, rótulo o ubicación…
Ubicaciones
En qué laboratorio está cada bloque y cada placa. Quién la manipuló por última vez queda en el historial.

Lab. Anatomía Patológica
- 19 placas
Lab. Histología
11 bloques - 172 placas
Lab. Anatomía Patológica
Placas (19)
Ratón	Placa	Técnica	Estado
9096245	set 2	IHQ/IF osteocalcina	no utilizable
9096245	set 4	IHQ/IF Runx2	terminada
9096245	set 10	IHQ/IF CD31	terminada
9096245	set 12	IHQ/IF osteocalcina	en técnica
9096245	set 25	IHQ/IF Runx2	terminada
9740174	set 2	IHQ/IF CD31	terminada
9740174	set 3	IHQ/IF CD31	terminada
9740174	set 9	IHQ/IF CD31	terminada
9740174	set 18	IHQ/IF CD31	terminada
9740174	set 19	IHQ/IF CD31	terminada
9740174	set 28	IHQ/IF CD31	terminada
9740174	set 36	IHQ/IF CD31	terminada
9794544	set 10	IHQ/IF osteocalcina	terminada
9794544	set 17	IHQ/IF CD31	terminada
9794544	set 18	IHQ/IF CD31	terminada
9794544	set 19	IHQ/IF osteocalcina	en técnica
9794544	set 26	IHQ/IF CD31	terminada
9794544	set 35	Otra: tinción especial	terminada
9096245	set 1	IHQ/IF Ki67	terminada
18. desde ubicacinoes no peudo apretar una plata, os ea aprieto un raton y me va  ala pestaña ratones supongo está ok. estoy casis egura que no puedo mover las placsa.

---

**G. Cierre y búsqueda**

19. ⚠️ *Docente:* en el ratón `9203523` (Esperando revisión SA), elige "Archivar" en la revisión SA. Debería quedar en Archivado y en Lab. Histología.
20. Busca `9746945` en el buscador. El historial debería tener todos los pasos anteriores, cada uno con su fecha y quién lo hizo.
21. Abre una placa del ratón `9096245` y escanea su QR con el celular. Debería abrir esa misma placa.

**Comentarios:**
extra: acá tipo ese mini dashboard general que sale esta ok pero es comor aro que sea lo principal... no se mejor donde poner esa info... Hola, Docente
Estado actual de los ratones y el trabajo pendiente.

3
En manejo (vivos o en EDTA)
5
En histología
2
Esperando revisión SA
3
Con placas en técnicas
Esa. y tipo el docente deberia tener la alerta de "esperando revision" (podriamos scrle el SA) porque es repsonavbiliad del docente.
19. el docente en la revision no elige archivar, archivar es un estado deerivado de haber terminado de cortar con un set en particular, porque significa q peudo guardar el casete de la muestra tipo a bodega y no tenerlo como pendiente eventualmetne. (no es relevante q vaya a bodega no e suna nueva ubiacion.) lo que tiene que hacer el docente en esta etpaa es decidir a qué va, eso tambien peude hacerlo TM. eso. o si hay que desgastar y luego hay re-revisino. y lo de en qué lugar quedan te dije que la ubicacion asume que queda donde mismo salvo algunas que serian tipo cuando se mandan a tecncia histologica, solo eos... el resto debe asumir que salend onde entran. lo otro. podriamos llamarle lab A y lab B no histolgoia y anaotmia paotlgica.
20. 
21. 

---


**comentarios generales**
- deberia poderse cambiar la ubicacion de las muestras idndependiente de si cambia de etapa o no.d e lo que sea placas o tejidos.

