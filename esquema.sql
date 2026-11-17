-- Base de datos del prototipo (SQLite). Un sujeto tiene bloques; un bloque tiene placas.
CREATE TABLE usuario (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('histologia', 'docente', 'estudiante'))
);

CREATE TABLE sujeto (
    id TEXT PRIMARY KEY,               -- número del ratón, como texto (conserva ceros iniciales)
    caja TEXT,
    sexo TEXT,
    fecha_nacimiento TEXT,
    fecha_cirugia TEXT,
    fecha_sacrificio TEXT,             -- NULL = vivo, en experimentación
    contenido_defecto_izq TEXT,        -- cada ratón tiene dos defectos
    contenido_defecto_der TEXT,
    tiempo_experimentacion TEXT,
    anestesia TEXT,
    experimento TEXT,
    grupo TEXT CHECK (grupo IN ('control', 'experimental')),
    lista TEXT,                        -- texto libre (significado no confirmado)
    tesis_responsable TEXT,
    ct_texto TEXT,                     -- texto libre
    comentarios TEXT
);

CREATE TABLE procesamiento_previo (
    id INTEGER PRIMARY KEY,
    sujeto_id TEXT NOT NULL REFERENCES sujeto(id),
    tipo TEXT NOT NULL,                -- desmineralización, inclusión previa, otro
    fecha TEXT,
    lugar TEXT,
    usuario_id INTEGER REFERENCES usuario(id)
);

CREATE TABLE estudio_imagen (
    id INTEGER PRIMARY KEY,
    sujeto_id TEXT NOT NULL REFERENCES sujeto(id),
    tipo TEXT NOT NULL DEFAULT 'microCT',
    lugar TEXT,
    fecha TEXT,
    vista_previa TEXT,                 -- ruta o enlace a PNG
    archivo_original TEXT              -- enlace externo (ej. Drive)
);

CREATE TABLE bloque (
    id TEXT PRIMARY KEY,
    sujeto_id TEXT NOT NULL REFERENCES sujeto(id),
    forma_llegada TEXT,                -- 'cubo de parafina' o 'cabeza en EDTA'
    fecha_recepcion TEXT,
    fecha_reinclusion TEXT,
    paso TEXT,                         -- paso actual del flujo (ver PASOS en servicios.py)
    estado TEXT CHECK (estado IN ('en lab', 'agotado', 'entregado')),
    ubicacion TEXT                     -- dónde está físicamente
);

CREATE TABLE placa (
    id INTEGER PRIMARY KEY,
    bloque_id TEXT NOT NULL REFERENCES bloque(id),
    serie TEXT NOT NULL CHECK (serie IN ('desgaste', 'set')),
    correlativo INTEGER NOT NULL,      -- vuelve a 1 al empezar la serie 'set'
    tipo_portaobjeto TEXT CHECK (tipo_portaobjeto IN ('normal', 'cargado')),
    protocolo TEXT,                    -- evaluación, estándar, estrella, corazón
    destino TEXT,                      -- HE o IHQ/IF (decidido al cortar)
    tecnica TEXT,                      -- técnica realizada; NULL si aún no se hace
    fecha_corte TEXT,
    fecha_tecnica TEXT,
    rotulo TEXT,                       -- nace al hacer la técnica; NULL antes
    ubicacion TEXT,                    -- dónde está físicamente
    estado TEXT CHECK (estado IN ('disponible', 'en técnica', 'terminada', 'perdida')),
    UNIQUE (bloque_id, serie, correlativo)
);

CREATE TABLE resultado_placa (
    id INTEGER PRIMARY KEY,
    placa_id INTEGER NOT NULL REFERENCES placa(id),
    usuario_id INTEGER REFERENCES usuario(id),
    tecnica_realizada TEXT,
    estado_final TEXT,                 -- realizada, con observaciones, en proceso, repetir, perdida
    comentario TEXT,
    fecha TEXT
);

CREATE TABLE imagen_placa (
    id INTEGER PRIMARY KEY,
    placa_id INTEGER NOT NULL REFERENCES placa(id),
    archivo TEXT,
    descripcion TEXT
);

-- Trazabilidad: quién hizo qué y cuándo.
CREATE TABLE evento (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuario(id),
    entidad TEXT NOT NULL,
    entidad_id TEXT NOT NULL,
    accion TEXT NOT NULL,
    fecha TEXT NOT NULL,
    detalle TEXT
);

-- Manejo: decalcificación en EDTA y sus cambios de solución.
CREATE TABLE decalcificacion (
    id INTEGER PRIMARY KEY,
    sujeto_id TEXT NOT NULL REFERENCES sujeto(id),
    fecha_inicio TEXT,
    fecha_fin TEXT                     -- NULL = en curso
);

CREATE TABLE cambio_edta (
    id INTEGER PRIMARY KEY,
    sujeto_id TEXT NOT NULL REFERENCES sujeto(id),
    fecha TEXT NOT NULL,
    usuario_id INTEGER REFERENCES usuario(id)
);
