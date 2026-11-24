"""Capa de lógica (decisión D1): ÚNICO archivo que toca la base de datos.

La pantalla (app.py) nunca escribe SQL; le pide los datos a estas funciones.
En la etapa 3 aquí se agregan las reglas de quién puede escribir qué.
"""
import hashlib
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd

DB = Path(__file__).parent / "data" / "prototipo.db"

# Si existe DATABASE_URL (Supabase), se usa PostgreSQL en la nube; si no, SQLite local.
# La contraseña de la base NUNCA va en el código: viene de .streamlit/secrets.toml o del entorno.
DATABASE_URL = os.environ.get("DATABASE_URL")
ES_POSTGRES = bool(DATABASE_URL)
_lectura_pg = None
DIAS_CAMBIO_EDTA = 3  # aviso si pasan más días que esto sin cambiar EDTA

PASOS_MANEJO = ["En experimentación", "Fijación en formalina", "Decalcificación"]
PASOS_HISTO = ["Recepción", "Reinclusión", "Desgaste", "Esperando revisión",
               "Corte de set", "Tinción HE", "Placas en técnicas", "Archivado"]
PASOS = PASOS_MANEJO + PASOS_HISTO

# Lo que probablemente viene después de cada paso (no todos los ratones pasan por todo).
SIGUIENTE = {
    "En experimentación": "Sacrificio y fijación en formalina",
    "Fijación en formalina": "Inicio de decalcificación",
    "Decalcificación": "Envío a histología",
    "Recepción": "Inclusión o reinclusión",
    "Reinclusión": "Desgaste",
    "Desgaste": "Revisión",
    "Esperando revisión": "Profundizar desgaste o corte de set",
    "Corte de set": "Tinción HE",
    "Tinción HE": "Placas a técnicas",
    "Placas en técnicas": "Archivo",
}


def _sql(sql):
    """Las consultas se escriben con '?'; PostgreSQL usa '%s'."""
    return sql.replace("?", "%s") if ES_POSTGRES else sql


def _conectar(autocommit=False):
    if ES_POSTGRES:
        import psycopg
        # prepare_threshold=None: compatible con el "pooler" de Supabase
        return psycopg.connect(DATABASE_URL, autocommit=autocommit, prepare_threshold=None)
    return sqlite3.connect(DB)


def _ejecutar_lectura(sql, params):
    global _lectura_pg
    if not ES_POSTGRES:
        con = sqlite3.connect(DB)
        try:
            cur = con.execute(sql, params)
            return [d[0] for d in cur.description], cur.fetchall()
        finally:
            con.close()
    # En la nube se reutiliza una conexión (abrir una por consulta es lento).
    for intento in range(2):
        try:
            if _lectura_pg is None or _lectura_pg.closed or _lectura_pg.broken:
                _lectura_pg = _conectar(autocommit=True)
            cur = _lectura_pg.execute(_sql(sql), params)
            return [d[0] for d in cur.description], cur.fetchall()
        except Exception:
            _lectura_pg = None
            if intento:
                raise


def _q(sql, params=()):
    columnas, filas = _ejecutar_lectura(sql, tuple(params))
    return pd.DataFrame(filas, columns=columnas)


def _uno(sql, params=()):
    df = _q(sql, params)
    return df.iloc[0].to_dict() if len(df) else None


# ---------------- Ratones ----------------
_RATONES = """
    SELECT s.id, s.grupo, s.contenido_defecto_izq AS izq, s.contenido_defecto_der AS der,
           s.fecha_sacrificio, b.id AS bloque, b.paso, b.ubicacion AS ubic_bloque,
           (SELECT COUNT(*) FROM placa p WHERE p.bloque_id = b.id AND p.tecnica = 'HE') AS he,
           (SELECT COUNT(*) FROM placa p WHERE p.bloque_id = b.id) AS placas,
           (SELECT COUNT(*) FROM decalcificacion d WHERE d.sujeto_id = s.id) AS n_dec,
           (SELECT e.accion || ' · ' || e.fecha FROM evento e
             WHERE (e.entidad='sujeto' AND e.entidad_id = s.id)
                OR (e.entidad='bloque' AND e.entidad_id = b.id)
             ORDER BY e.fecha DESC, e.id DESC LIMIT 1) AS ultimo
    FROM sujeto s LEFT JOIN bloque b ON b.sujeto_id = s.id
"""


def _paso(fila):
    if pd.isna(fila["fecha_sacrificio"]):
        return "En experimentación"
    if pd.isna(fila["bloque"]):
        return "Decalcificación" if fila["n_dec"] else "Fijación en formalina"
    return fila["paso"]


LABS = ["Bioterio", "Lab. A", "Lab. B"]
ORDENES = {"Número": "id", "Paso": "orden_paso", "Último trabajo (reciente primero)": "ultimo"}


def _ubicacion(fila):
    if pd.isna(fila["fecha_sacrificio"]) or pd.isna(fila["bloque"]):
        return "Bioterio"
    return fila["ubic_bloque"]


def ratones(busqueda="", paso="Todos", orden="Número"):
    df = _q(_RATONES + " ORDER BY s.id")
    df["paso_actual"] = df.apply(_paso, axis=1)
    df["donde"] = df.apply(_ubicacion, axis=1)
    df["orden_paso"] = df["paso_actual"].map(PASOS.index)
    df["fecha_ultimo"] = df["ultimo"].fillna("").str.split(" · ").str[-1]
    if orden == "Último trabajo (reciente primero)":
        df = df.sort_values("fecha_ultimo", ascending=False)
    elif orden == "Paso":
        df = df.sort_values(["orden_paso", "id"])
    if busqueda:
        df = df[df["id"].str.contains(busqueda.strip())]
    if paso != "Todos":
        df = df[df["paso_actual"] == paso]
    return df


def raton(sid):
    df = _q(_RATONES + " WHERE s.id = ?", (sid,))
    if df.empty:
        return None
    fila = df.iloc[0].to_dict()
    fila["paso_actual"] = _paso(fila)
    fila["donde"] = _ubicacion(fila)
    fila["datos"] = _uno("SELECT * FROM sujeto WHERE id = ?", (sid,))
    fila["bloque_info"] = _uno("SELECT * FROM bloque WHERE sujeto_id = ?", (sid,))
    return fila


def conteo_por_paso():
    df = ratones()
    return {p: int((df["paso_actual"] == p).sum()) for p in PASOS}


# ---------------- Manejo ----------------
def decalcificacion(sid):
    d = _uno("SELECT * FROM decalcificacion WHERE sujeto_id = ?", (sid,))
    cambios = _q("""SELECT c.fecha AS "Fecha", u.nombre AS "Quién" FROM cambio_edta c
                    LEFT JOIN usuario u ON u.id = c.usuario_id
                    WHERE c.sujeto_id = ? ORDER BY c.fecha DESC""", (sid,))
    return d, cambios


def alertas_edta():
    """Ratones con decalcificación en curso y su último cambio de EDTA."""
    df = _q("""
        SELECT d.sujeto_id AS id, d.fecha_inicio,
               (SELECT MAX(c.fecha) FROM cambio_edta c WHERE c.sujeto_id = d.sujeto_id) AS ultimo_cambio
        FROM decalcificacion d WHERE d.fecha_fin IS NULL""")
    if df.empty:
        return df
    hoy = pd.Timestamp(date.today())
    ref = pd.to_datetime(df["ultimo_cambio"].fillna(df["fecha_inicio"]))
    df["dias"] = (hoy - ref).dt.days
    df["toca_cambio"] = df["dias"] >= DIAS_CAMBIO_EDTA
    return df.sort_values("dias", ascending=False)


def alertas_histologia():
    """Pendientes de histología: revisiones por hacer y sets indicados sin cortar."""
    df = ratones()
    return {"revision": df[df["paso_actual"] == "Esperando revisión"]["id"].tolist(),
            "corte": df[df["paso_actual"] == "Corte de set"]["id"].tolist()}


# ---------------- Placas ----------------
def placas(sid):
    df = _q("""
        SELECT p.id, p.serie, p.correlativo, p.tipo_portaobjeto, p.protocolo, p.destino,
               p.tecnica, p.fecha_corte, p.fecha_tecnica, p.rotulo, p.estado, p.ubicacion,
               r.estado_final AS resultado, r.comentario, u.nombre AS quien
        FROM placa p JOIN bloque b ON b.id = p.bloque_id
        LEFT JOIN resultado_placa r ON r.id = (SELECT MAX(id) FROM resultado_placa WHERE placa_id = p.id)
        LEFT JOIN usuario u ON u.id = r.usuario_id
        WHERE b.sujeto_id = ?
        ORDER BY CASE p.serie WHEN 'desgaste' THEN 0 ELSE 1 END, p.correlativo""", (sid,))
    return df.astype(object).where(df.notna(), None)  # vacíos como None, no NaN


def resultado_placa(pid):
    return _uno("""SELECT r.*, u.nombre FROM resultado_placa r
                   LEFT JOIN usuario u ON u.id = r.usuario_id WHERE r.placa_id = ?""", (pid,))


def historial_placa(pid):
    return _q("""SELECT e.fecha AS "Fecha", e.accion AS "Acción", e.detalle AS "Detalle", u.nombre AS "Quién"
                 FROM evento e LEFT JOIN usuario u ON u.id = e.usuario_id
                 WHERE e.entidad = 'placa' AND e.entidad_id = ? ORDER BY e.fecha""", (str(pid),))


def placas_para_tecnicas():
    """Placas de set sin técnica todavía, agrupadas por ratón."""
    return _q("""
        SELECT b.sujeto_id AS "Ratón", MIN(p.protocolo) AS "Protocolo",
               SUM(CASE WHEN p.tipo_portaobjeto = 'cargado' THEN 1 ELSE 0 END) AS "Cargadas disponibles",
               SUM(CASE WHEN p.tipo_portaobjeto = 'normal' THEN 1 ELSE 0 END) AS "Normales disponibles",
               MIN(p.ubicacion) AS "Ubicación"
        FROM placa p JOIN bloque b ON b.id = p.bloque_id
        WHERE p.serie = 'set' AND p.tecnica IS NULL AND p.estado = 'disponible'
          AND b.paso IN ('Placas en técnicas', 'Archivado')
        GROUP BY b.sujeto_id ORDER BY b.sujeto_id""")


def resultados_recientes(resultado="Todos"):
    df = _q("""
        SELECT r.fecha AS "Fecha", b.sujeto_id AS "Ratón", p.correlativo AS "Placa",
               r.tecnica_realizada AS "Técnica", r.estado_final AS "Resultado",
               r.comentario AS "Comentario", u.nombre AS "Quién"
        FROM resultado_placa r JOIN placa p ON p.id = r.placa_id
        JOIN bloque b ON b.id = p.bloque_id LEFT JOIN usuario u ON u.id = r.usuario_id
        ORDER BY r.fecha DESC""")
    return df if resultado == "Todos" else df[df["Resultado"] == resultado]


# ---------------- Historial ----------------
def historial(sid):
    return _q("""
        SELECT e.fecha AS "Fecha", e.accion AS "Acción", e.detalle AS "Detalle", u.nombre AS "Quién"
        FROM evento e LEFT JOIN usuario u ON u.id = e.usuario_id
        WHERE (e.entidad = 'sujeto' AND e.entidad_id = ?)
           OR (e.entidad = 'bloque' AND e.entidad_id IN (SELECT id FROM bloque WHERE sujeto_id = ?))
           OR (e.entidad = 'placa' AND e.entidad_id IN (
                 SELECT CAST(p.id AS TEXT) FROM placa p JOIN bloque b ON b.id = p.bloque_id
                 WHERE b.sujeto_id = ?))
        ORDER BY e.fecha DESC, e.id DESC""", (sid, sid, sid))


def imagenologia(sid):
    return _q("SELECT * FROM estudio_imagen WHERE sujeto_id = ? ORDER BY fecha", (sid,))


def procesamiento_previo(sid):
    return _q("""SELECT tipo AS "Procedimiento", fecha AS "Fecha", lugar AS "Lugar"
                 FROM procesamiento_previo WHERE sujeto_id = ? ORDER BY fecha""", (sid,))


# =====================================================================
# ETAPA 3 · Usuarios, permisos y registro de acciones
# =====================================================================

# Qué puede registrar cada rol. La pantalla oculta lo que no corresponde,
# pero la regla se valida AQUÍ (capa intermedia), no en la pantalla.
TODAS = {"ingresar_raton", "sacrificio", "cambio_edta", "enviar_histologia", "paso_histologia", "revision_sa",
         "ubicacion", "tecnica_placa"}
PERMISOS = {
    # Según cómo se trabaja hoy en el laboratorio:
    "docente": {"ingresar_raton", "sacrificio", "revision_sa", "ubicacion", "cambio_edta", "tecnica_placa"},
    "tm": {"paso_histologia", "revision_sa", "tecnica_placa", "ubicacion"},
    "estudiante": {"cambio_edta", "enviar_histologia", "tecnica_placa", "ubicacion"},
    "admin": TODAS,
}
NOMBRE_ROL = {"docente": "Docente", "tm": "TM", "estudiante": "Estudiante", "admin": "Admin"}

PROTOCOLOS = {
    "estándar": ([("HE", 3), ("IHQ/IF", 3), ("HE", 3), ("IHQ/IF", 3), ("HE", 3)], {1, 8, 15}),
    "estrella": ([("IHQ/IF", 4), ("HE", 4)] * 2 + [("IHQ/IF", 4), ("HE", 3)], {5, 21}),
    "corazón": ([("IHQ/IF", 4), ("HE", 4)] * 4 + [("IHQ/IF", 4), ("HE", 3)], {5, 21, 39}),
}
RESULTADOS = ["realizada", "realizada con observaciones", "en proceso", "repetir"]


def cifrar(clave, uid):
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), f"sal-{uid}".encode(), 100_000).hex()


def nombres_usuarios():
    return _q("SELECT nombre FROM usuario ORDER BY id")["nombre"].tolist()


def usuarios_login():
    """Para el login: el rol primero y, si hay varios con el mismo rol, el nombre."""
    df = _q("SELECT nombre, rol FROM usuario ORDER BY id")
    return [{"nombre": f["nombre"],
             "texto": f["nombre"] if f["nombre"].startswith(NOMBRE_ROL.get(f["rol"], f["rol"]))
             else f'{NOMBRE_ROL.get(f["rol"], f["rol"])} ({f["nombre"]})'} for f in df.to_dict("records")]


def autenticar(nombre, clave):
    u = _uno("SELECT id, nombre, rol, clave_hash FROM usuario WHERE nombre = ?", (nombre,))
    if u and u["clave_hash"] == cifrar(clave, int(u["id"])):
        return {"id": int(u["id"]), "nombre": u["nombre"], "rol": u["rol"]}
    return None


def puede(usuario, accion):
    return bool(usuario) and accion in PERMISOS.get(usuario["rol"], set())


def _exigir(usuario, accion):
    if not puede(usuario, accion):
        raise PermissionError(f"El rol {NOMBRE_ROL.get(usuario['rol'], '?')} no puede realizar esta acción.")


class _Con:
    """Envoltorio mínimo para escribir igual en SQLite y PostgreSQL."""
    def __init__(self, crudo):
        self.crudo = crudo

    def execute(self, sql, params=()):
        cur = self.crudo.cursor()
        cur.execute(_sql(sql), tuple(params))
        return cur


class _Escritura:
    """Abre la base, hace todo junto (o nada si hay error) y cierra."""
    def __enter__(self):
        self.crudo = _conectar()
        return _Con(self.crudo)

    def __exit__(self, tipo, *_):
        if tipo is None:
            self.crudo.commit()
        else:
            self.crudo.rollback()
        self.crudo.close()


def _evento(con, u, entidad, eid, accion, fecha, detalle=""):
    con.execute("INSERT INTO evento (usuario_id, entidad, entidad_id, accion, fecha, detalle)"
                " VALUES (?,?,?,?,?,?)", (u["id"], entidad, str(eid), accion, fecha.isoformat(),
                                          f"{detalle} [registrado {datetime.now():%d/%m/%y %H:%M}]".strip()))


def _rotulo(con, bloque_id, tecnica, fecha, corr):
    sid = con.execute("SELECT sujeto_id FROM bloque WHERE id = ?", (bloque_id,)).fetchone()[0]
    return f"{sid} | {tecnica} | {fecha:%d/%m/%y} | {corr}"


def _bloque(con, bid):
    fila = con.execute("SELECT paso, sujeto_id FROM bloque WHERE id = ?", (bid,)).fetchone()
    if not fila:
        raise ValueError("Bloque no encontrado.")
    return fila


def _exigir_paso(con, bid, *pasos):
    paso = _bloque(con, bid)[0]
    if paso not in pasos:
        raise ValueError(f"El bloque está en «{paso}»; esta acción corresponde a: {', '.join(pasos)}.")


# ---------------- Ingreso y edición de ratones ----------------
CONTENIDOS = ["vacío", "células 200.000", "andamio", "andamio + células 200.000"]
CAMPOS_RATON = ["sexo", "fecha_nacimiento", "fecha_cirugia", "contenido_defecto_izq", "contenido_defecto_der",
                "tiempo_experimentacion", "anestesia", "comentarios"]


def _validar_raton(d):
    if not d.get("fecha_cirugia"):
        raise ValueError("La fecha de cirugía es obligatoria.")
    if not d.get("contenido_defecto_izq") or not d.get("contenido_defecto_der"):
        raise ValueError("Indica el contenido de ambos defectos.")
    d["grupo"] = "control" if d["contenido_defecto_izq"] == d["contenido_defecto_der"] == "vacío" else "experimental"
    return d


def ingresar_raton(u, sid, datos):
    _exigir(u, "ingresar_raton")
    sid = sid.strip()
    if not sid.isdigit():
        raise ValueError("El número del ratón debe tener solo dígitos.")
    d = _validar_raton({k: (datos.get(k) or None) for k in CAMPOS_RATON})
    with _Escritura() as con:
        if con.execute("SELECT 1 FROM sujeto WHERE id = ?", (sid,)).fetchone():
            raise ValueError(f"Ya existe el ratón {sid}.")
        cols = ["id"] + CAMPOS_RATON + ["grupo"]
        con.execute(f"INSERT INTO sujeto ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                    [sid] + [d[k] for k in CAMPOS_RATON] + [d["grupo"]])
        _evento(con, u, "sujeto", sid, "Cirugía: defectos bilaterales", date.fromisoformat(d["fecha_cirugia"]),
                f"izq.: {d['contenido_defecto_izq']} / der.: {d['contenido_defecto_der']}")
    return sid


def editar_raton(u, sid, datos):
    _exigir(u, "ingresar_raton")
    d = _validar_raton({k: (datos.get(k) or None) for k in CAMPOS_RATON})
    with _Escritura() as con:
        con.execute(f"UPDATE sujeto SET {', '.join(k + ' = ?' for k in CAMPOS_RATON)}, grupo = ? WHERE id = ?",
                    [d[k] for k in CAMPOS_RATON] + [d["grupo"], sid])
        _evento(con, u, "sujeto", sid, "Datos del ratón editados", date.today())


# ---------------- Manejo ----------------
def registrar_sacrificio(u, sid, fecha):
    _exigir(u, "sacrificio")
    with _Escritura() as con:
        con.execute("UPDATE sujeto SET fecha_sacrificio = ? WHERE id = ?", (fecha.isoformat(), sid))
        _evento(con, u, "sujeto", sid, "Sacrificio y fijación en formalina", fecha)


def iniciar_decalcificacion(u, sid, fecha):
    _exigir(u, "cambio_edta")
    with _Escritura() as con:
        if con.execute("SELECT 1 FROM decalcificacion WHERE sujeto_id = ?", (sid,)).fetchone():
            raise ValueError("Este ratón ya tiene decalcificación registrada.")
        con.execute("INSERT INTO decalcificacion (sujeto_id, fecha_inicio) VALUES (?,?)", (sid, fecha.isoformat()))
        _evento(con, u, "sujeto", sid, "Inicio decalcificación EDTA", fecha)


def registrar_cambio_edta(u, sid, fecha):
    _exigir(u, "cambio_edta")
    with _Escritura() as con:
        if not con.execute("SELECT 1 FROM decalcificacion WHERE sujeto_id = ? AND fecha_fin IS NULL", (sid,)).fetchone():
            raise ValueError("Este ratón no tiene una decalcificación en curso.")
        con.execute("INSERT INTO cambio_edta (sujeto_id, fecha, usuario_id) VALUES (?,?,?)",
                    (sid, fecha.isoformat(), u["id"]))
        _evento(con, u, "sujeto", sid, "Cambio de EDTA", fecha)


def enviar_a_histologia(u, sid, fecha, forma):
    """Llega a histología como 'cubo de parafina' o 'cabeza en EDTA' (sigue decalcificando)."""
    _exigir(u, "enviar_histologia")
    bid = f"{sid}-B1"
    with _Escritura() as con:
        if con.execute("SELECT 1 FROM bloque WHERE id = ?", (bid,)).fetchone():
            raise ValueError("Este ratón ya está en histología.")
        if forma == "cubo de parafina":
            con.execute("UPDATE decalcificacion SET fecha_fin = ? WHERE sujeto_id = ? AND fecha_fin IS NULL",
                        (fecha.isoformat(), sid))
            _evento(con, u, "sujeto", sid, "Fin decalcificación", fecha)
        paso = "Recepción" if forma == "cabeza en EDTA" else "Reinclusión"
        ubic = "Lab. A"
        con.execute("INSERT INTO bloque (id, sujeto_id, forma_llegada, fecha_recepcion, paso, estado, ubicacion)"
                    " VALUES (?,?,?,?,?,?,?)", (bid, sid, forma, fecha.isoformat(), paso, "en lab", ubic))
        _evento(con, u, "bloque", bid, f"Recepción en histología ({forma})", fecha)


# ---------------- Histología ----------------
def registrar_inclusion(u, bid, fecha):
    _exigir(u, "paso_histologia")
    with _Escritura() as con:
        _exigir_paso(con, bid, "Recepción", "Reinclusión")
        paso, sid = _bloque(con, bid)
        con.execute("UPDATE decalcificacion SET fecha_fin = ? WHERE sujeto_id = ? AND fecha_fin IS NULL",
                    (fecha.isoformat(), sid))
        con.execute("UPDATE bloque SET fecha_reinclusion = ?, paso = 'Desgaste', ubicacion = 'Lab. A'"
                    " WHERE id = ?", (fecha.isoformat(), bid))
        _evento(con, u, "bloque", bid, "Inclusión en casete" if paso == "Recepción" else "Reinclusión en casete", fecha)


def cortar_desgaste(u, bid, fecha, n):
    """Corta N placas de desgaste (sin teñir). El bloque sigue en Desgaste hasta teñir."""
    _exigir(u, "paso_histologia")
    n = int(n)
    if not 1 <= n <= 20:
        raise ValueError("Indica cuántas placas cortaste (1 a 20).")
    with _Escritura() as con:
        _exigir_paso(con, bid, "Desgaste")
        ultimo = con.execute("SELECT COALESCE(MAX(correlativo), 0) FROM placa WHERE bloque_id = ? AND serie = 'desgaste'",
                             (bid,)).fetchone()[0]
        for corr in range(ultimo + 1, ultimo + n + 1):
            con.execute("INSERT INTO placa (bloque_id, serie, correlativo, tipo_portaobjeto, protocolo, destino,"
                        " fecha_corte, ubicacion, estado) VALUES (?,?,?,?,?,?,?,?,?)",
                        (bid, "desgaste", corr, "normal", "evaluación", "HE", fecha.isoformat(), "Lab. A", "disponible"))
        _evento(con, u, "bloque", bid, f"Desgaste: corte de {n} placa(s) ({ultimo + 1}-{ultimo + n})", fecha)


def tenir_desgaste(u, bid, fecha, correlativos):
    """Tiñe con HE las placas de desgaste elegidas y deja el bloque esperando revisión."""
    _exigir(u, "paso_histologia")
    if not correlativos:
        raise ValueError("Marca al menos una placa para teñir.")
    with _Escritura() as con:
        _exigir_paso(con, bid, "Desgaste")
        for corr in correlativos:
            con.execute("UPDATE placa SET tecnica = 'HE', fecha_tecnica = ?, rotulo = ?, estado = 'terminada'"
                        " WHERE bloque_id = ? AND serie = 'desgaste' AND correlativo = ? AND tecnica IS NULL",
                        (fecha.isoformat(), _rotulo(con, bid, "HE", fecha, corr), bid, corr))
        con.execute("UPDATE bloque SET paso = 'Esperando revisión' WHERE id = ?", (bid,))
        _evento(con, u, "bloque", bid, f"Desgaste: HE de placa(s) {sorted(correlativos)}", fecha)


def registrar_revision_sa(u, bid, fecha, decision, protocolo=None):
    _exigir(u, "revision_sa")
    destino = {"Profundizar desgaste": "Desgaste", "Indicar set de corte": "Corte de set"}
    if decision not in destino:
        raise ValueError("Decisión no válida.")
    with _Escritura() as con:
        _exigir_paso(con, bid, "Esperando revisión")
        con.execute("UPDATE bloque SET paso = ? WHERE id = ?", (destino[decision], bid))
        detalle = decision + (f": set {protocolo}" if decision == "Indicar set de corte" and protocolo else "")
        _evento(con, u, "bloque", bid, "Revisión", fecha, detalle)


def cortar_set(u, bid, fecha, protocolo):
    _exigir(u, "paso_histologia")
    grupos, _ = PROTOCOLOS[protocolo]
    with _Escritura() as con:
        _exigir_paso(con, bid, "Corte de set")
        corr = 0
        for destino, cantidad in grupos:
            for _ in range(cantidad):
                corr += 1
                con.execute("INSERT INTO placa (bloque_id, serie, correlativo, tipo_portaobjeto, protocolo, destino,"
                            " fecha_corte, ubicacion, estado) VALUES (?,?,?,?,?,?,?,?,?)",
                            (bid, "set", corr, "normal" if destino == "HE" else "cargado", protocolo, destino,
                             fecha.isoformat(), "Lab. A", "disponible"))
        con.execute("UPDATE bloque SET paso = 'Tinción HE' WHERE id = ?", (bid,))
        _evento(con, u, "bloque", bid, f"Corte set {protocolo} ({corr} placas)", fecha)


def tenir_he_set(u, bid, fecha):
    _exigir(u, "paso_histologia")
    with _Escritura() as con:
        _exigir_paso(con, bid, "Tinción HE")
        protocolo = con.execute("SELECT protocolo FROM placa WHERE bloque_id = ? AND serie = 'set' LIMIT 1",
                                (bid,)).fetchone()[0]
        tenidas = sorted(PROTOCOLOS[protocolo][1])
        for corr in tenidas:
            con.execute("UPDATE placa SET tecnica = 'HE', fecha_tecnica = ?, rotulo = ?, estado = 'terminada'"
                        " WHERE bloque_id = ? AND serie = 'set' AND correlativo = ?",
                        (fecha.isoformat(), _rotulo(con, bid, "HE", fecha, corr), bid, corr))
        con.execute("UPDATE bloque SET paso = 'Placas en técnicas' WHERE id = ?", (bid,))
        _evento(con, u, "bloque", bid, f"Tinción HE placas {tenidas}", fecha)


def archivar(u, bid, fecha):
    _exigir(u, "paso_histologia")
    with _Escritura() as con:
        _exigir_paso(con, bid, "Placas en técnicas")
        con.execute("UPDATE bloque SET paso = 'Archivado' WHERE id = ?", (bid,))
        _evento(con, u, "bloque", bid, "Archivado (set terminado)", fecha)


def mover_bloque(u, bid, ubicacion, fecha):
    _exigir(u, "ubicacion")
    with _Escritura() as con:
        con.execute("UPDATE bloque SET ubicacion = ? WHERE id = ?", (ubicacion, bid))
        _evento(con, u, "bloque", bid, "Cambio de ubicación del bloque", fecha, ubicacion)


# ---------------- Placas ----------------
def registrar_tecnica(u, pid, fecha, tecnica, resultado, comentario):
    _exigir(u, "tecnica_placa")
    if resultado not in RESULTADOS:
        raise ValueError("Resultado no válido.")
    if not tecnica.strip():
        raise ValueError("Indica qué técnica se hizo.")
    with _Escritura() as con:
        fila = con.execute("SELECT bloque_id, correlativo, tecnica, estado FROM placa WHERE id = ?", (pid,)).fetchone()
        if not fila:
            raise ValueError("Placa no encontrada.")
        bid, corr, actual, estado_actual = fila
        if estado_actual == "inutilizable":
            raise ValueError("Esta placa está marcada como inutilizable.")
        if actual == "HE":
            raise ValueError("Esta placa ya está teñida con HE.")
        estado = "en técnica" if resultado == "en proceso" else "terminada"
        con.execute("UPDATE placa SET tecnica = ?, fecha_tecnica = ?, rotulo = ?, estado = ?"
                    " WHERE id = ?", (tecnica, fecha.isoformat(), _rotulo(con, bid, tecnica, fecha, corr),
                                      estado, pid))
        con.execute("INSERT INTO resultado_placa (placa_id, usuario_id, tecnica_realizada, estado_final, comentario, fecha)"
                    " VALUES (?,?,?,?,?,?)", (pid, u["id"], tecnica, resultado, comentario, fecha.isoformat()))
        _evento(con, u, "placa", pid, f"Técnica: {tecnica}", fecha, f"{resultado}. {comentario}".strip())


def marcar_inutilizable(u, pid, fecha, comentario=""):
    """La placa queda registrada pero ya no se puede usar (rota, perdida, desprendida...)."""
    _exigir(u, "tecnica_placa")
    with _Escritura() as con:
        if not con.execute("SELECT 1 FROM placa WHERE id = ?", (pid,)).fetchone():
            raise ValueError("Placa no encontrada.")
        con.execute("UPDATE placa SET estado = 'inutilizable' WHERE id = ?", (pid,))
        con.execute("INSERT INTO resultado_placa (placa_id, usuario_id, tecnica_realizada, estado_final, comentario, fecha)"
                    " VALUES (?,?,?,?,?,?)", (pid, u["id"], None, "inutilizable", comentario, fecha.isoformat()))
        _evento(con, u, "placa", pid, "Placa inutilizable", fecha, comentario)


def mover_varios(u, placas_ids, bloques_ids, ubicacion, fecha):
    """Mueve varias placas y/o bloques a la vez (sin cambiar de etapa)."""
    _exigir(u, "ubicacion")
    if ubicacion not in LABS:
        raise ValueError("Laboratorio no válido.")
    if not placas_ids and not bloques_ids:
        raise ValueError("Marca al menos una placa o bloque.")
    with _Escritura() as con:
        for pid in placas_ids:
            con.execute("UPDATE placa SET ubicacion = ? WHERE id = ?", (ubicacion, pid))
            _evento(con, u, "placa", pid, "Cambio de ubicación de la placa", fecha, ubicacion)
        for bid in bloques_ids:
            con.execute("UPDATE bloque SET ubicacion = ? WHERE id = ?", (ubicacion, bid))
            _evento(con, u, "bloque", bid, "Cambio de ubicación del bloque", fecha, ubicacion)


def movimientos_placa(pid):
    return _q("""SELECT e.fecha AS "Fecha", e.detalle AS "Detalle", u.nombre AS "Quién"
                 FROM evento e LEFT JOIN usuario u ON u.id = e.usuario_id
                 WHERE e.entidad = 'placa' AND e.entidad_id = ? AND e.accion LIKE 'Cambio de ubicación%'
                 ORDER BY e.fecha""", (str(pid),))


def mover_placa(u, pid, ubicacion, fecha):
    _exigir(u, "ubicacion")
    if not ubicacion.strip():
        raise ValueError("Indica la nueva ubicación.")
    with _Escritura() as con:
        con.execute("UPDATE placa SET ubicacion = ? WHERE id = ?", (ubicacion, pid))
        _evento(con, u, "placa", pid, "Cambio de ubicación de la placa", fecha, ubicacion)


# =====================================================================
# Ubicaciones (solo laboratorio) y búsqueda
# =====================================================================

def arbol_ubicaciones():
    """Conteo por laboratorio: ratones (Bioterio), bloques y placas."""
    filas = _q("""SELECT ubicacion, 'placa' AS tipo FROM placa WHERE ubicacion IS NOT NULL
                  UNION ALL SELECT ubicacion, 'bloque' FROM bloque WHERE ubicacion IS NOT NULL""")
    arbol = {lab: {"raton": 0, "placa": 0, "bloque": 0} for lab in LABS}
    for _, f in filas.iterrows():
        arbol.setdefault(f["ubicacion"], {"raton": 0, "placa": 0, "bloque": 0})[f["tipo"]] += 1
    arbol["Bioterio"]["raton"] = int((ratones()["donde"] == "Bioterio").sum())
    return arbol


def ratones_en_bioterio():
    df = ratones()
    return df[df["donde"] == "Bioterio"]


def en_ubicacion(lab):
    """Bloques y placas en un laboratorio dado."""
    placas_ = _q("""SELECT p.id, b.sujeto_id, p.serie, p.correlativo, p.tecnica, p.destino, p.estado, p.ubicacion
                    FROM placa p JOIN bloque b ON b.id = p.bloque_id WHERE p.ubicacion = ?
                    ORDER BY b.sujeto_id, p.serie, p.correlativo""", (lab,))
    bloques_ = _q("SELECT id, sujeto_id, paso, ubicacion FROM bloque WHERE ubicacion = ? ORDER BY ubicacion",
                  (lab,))
    return bloques_, placas_


def placa(pid):
    d = _uno("""SELECT p.*, b.sujeto_id, r.estado_final AS resultado, r.comentario, u.nombre AS quien
                FROM placa p JOIN bloque b ON b.id = p.bloque_id
                LEFT JOIN resultado_placa r ON r.id = (SELECT MAX(id) FROM resultado_placa WHERE placa_id = p.id)
                LEFT JOIN usuario u ON u.id = r.usuario_id WHERE p.id = ?""", (pid,))
    return {k: (None if pd.isna(v) else v) for k, v in d.items()} if d else None


def eventos_recientes(n=15):
    return _q("""
        SELECT e.fecha, e.accion, e.detalle, e.entidad, e.entidad_id, u.nombre AS quien,
               COALESCE(CASE e.entidad WHEN 'sujeto' THEN e.entidad_id END,
                        (SELECT sujeto_id FROM bloque WHERE id = e.entidad_id),
                        (SELECT b.sujeto_id FROM placa p JOIN bloque b ON b.id = p.bloque_id
                          WHERE CAST(p.id AS TEXT) = e.entidad_id)) AS sujeto_id
        FROM evento e LEFT JOIN usuario u ON u.id = e.usuario_id
        ORDER BY e.fecha DESC, e.id DESC LIMIT ?""", (n,))


def buscar(texto):
    """Busca ratones por número y placas por rótulo o ubicación."""
    t = f"%{texto.strip()}%"
    r = _q("SELECT id FROM sujeto WHERE id LIKE ? ORDER BY id", (t,))
    p = _q("""SELECT p.id, b.sujeto_id, p.serie, p.correlativo, p.rotulo, p.ubicacion
              FROM placa p JOIN bloque b ON b.id = p.bloque_id
              WHERE p.rotulo LIKE ? OR p.ubicacion LIKE ? ORDER BY b.sujeto_id, p.id LIMIT 50""", (t, t))
    return r, p


def linaje(sid):
    """Árbol: ratón → bloque → series → placas (con su estado)."""
    bl = _uno("SELECT * FROM bloque WHERE sujeto_id = ?", (sid,))
    if not bl:
        return None
    ps = placas(sid)
    series = []
    for serie, nombre in (("desgaste", "Desgaste (evaluación)"), ("set", "Set de corte")):
        sub = ps[ps["serie"] == serie]
        if len(sub):
            proto = sub["protocolo"].iloc[0] if serie == "set" else None
            series.append({"nombre": nombre + (f" ({proto})" if proto else ""),
                           "placas": sub.to_dict("records")})
    return {"bloque": bl, "series": series}
