# Problema

En un proyecto de investigación se generan defectos óseos en cráneos de ratón y se aplican
distintos tratamientos para comparar su efecto entre condiciones experimentales. Cada sujeto
pasa por varias etapas: tratamiento, imagenología (microCT), procesamiento histológico
(inclusión, corte y tinción) y después técnicas como inmunofluorescencia. Hoy la información
de cada etapa está fragmentada entre distintas personas y registros, y es difícil saber en qué
va cada muestra y a qué técnica se destina cada placa.

Propuesta: una aplicación web, accesible también desde el celular, que reúna en un solo lugar
la ficha de cada sujeto, sus muestras y placas, la técnica asignada a cada placa con su rótulo,
sus imágenes (histología y microCT) y un historial de quién hizo qué y cuándo. La docente
responsable, los estudiantes y la responsable de histología acceden con su usuario, y cada
uno registra la etapa que le corresponde.

Datos: los sujetos son ratones, pero la investigación no está publicada, por lo que el
prototipo usa solo datos ficticios.

## Por qué es transferible a pacientes

| Investigación | Equivalente clínico |
|---|---|
| Sujeto (ratón) | Paciente |
| Condición experimental | Diagnóstico / tratamiento |
| MicroCT | Estudio radiológico (TC) |
| Bloque y placas | Bloques y placas de una biopsia en anatomía patológica |
| Técnicas posteriores (IHQ/IF) | Técnicas complementarias (IHQ) |
| Historial de eventos | Trazabilidad de la muestra |

Elegí un problema de investigación por dos razones: es parte de mi trabajo diario, no solo la
clínica, y supuse que la mayoría elegiría un problema clínico. Además, la parte del proyecto que
me toca, el procesamiento histológico, es prácticamente lo mismo que se hace en un laboratorio de
anatomía patológica: recibir, procesar, cortar, teñir, rotular y ubicar cada muestra.

La investigación suele ser más desordenada que la clínica. No hay estándares de acreditación ni
prestaciones que cobrar, así que cada laboratorio registra como puede: cuadernos, planillas sueltas
o la memoria de quien hizo el trabajo. Aun así, muchas veces se trabaja con muestras humanas y
participa mucha gente: investigadores presionados por publicar y conseguir financiamiento,
estudiantes cuyas tesis dependen de los resultados y personal contratado por proyectos. Cuando
alguien se va, la información que solo tenía esa persona se pierde.

En anatomía patológica, la trazabilidad es crítica: saber en qué etapa está cada biopsia, desde
cuándo y quién la tiene. Perder una biopsia es un evento centinela. Además, muchos protocolos
dependen del tiempo. Si el sistema dice que una muestra entró a formalina ayer cuando fue hoy,
puedo asumir que ya está fijada y no lo está. Si alguien olvida revisar su cuaderno o se ausenta
por licencia, un tejido puede quedar días de más en decalcificación ácida y volverse no
diagnosticable.

Por eso, aunque el prototipo nace en investigación con ratones, su lógica es transferible a un
servicio de anatomía patológica y a otros procesos con muestras, plazos y muchas personas, como
los ensayos clínicos.