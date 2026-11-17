"""Capa de lógica (decisión D1): ÚNICO archivo que toca la base de datos.

La pantalla (app.py) nunca escribe SQL; le pide los datos a estas funciones.
En la etapa 3 aquí se agregan las reglas de quién puede escribir qué.
"""
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

DB = Path(__file__).parent / "data" / "prototipo.db"
DIAS_CAMBIO_EDTA = 3  # aviso si pasan más días que esto sin cambiar EDTA

PASOS_MANEJO = ["En experimentación", "Decalcificación"]
PASOS_HISTO = ["Recepción", "Reinclusión", "Desgaste", "Esperando revisión SA",
               "Corte de set", "Tinción HE", "Placas en técnicas", "Archivado"]
PASOS = PASOS_MANEJO + PASOS_HISTO

# Lo que probablemente viene después de cada paso (no todos los ratones pasan por todo).
SIGUIENTE = {
    "En experimentación": "Sacrificio y decalcificación",
    "Decalcificación": "Envío a histología",
    "Recepción": "Inclusión o reinclusión",
    "Reinclusión": "Desgaste",
    "Desgaste": "Revisión SA",
    "Esperando revisión SA": "Profundizar desgaste o corte de set (según SA)",
    "Corte de set": "Tinción HE",
    "Tinción HE": "Placas a técnicas",
    "Placas en técnicas": "Archivo",
}


def _q(sql, params=()):
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query(sql, con, params=params)


def _uno(sql, params=()):
    df = _q(sql, params)
    return df.iloc[0].to_dict() if len(df) else None


# ---------------- Ratones ----------------
_RATONES = """
    SELECT s.id, s.grupo, s.contenido_defecto_izq AS izq, s.contenido_defecto_der AS der,
           s.fecha_sacrificio, b.id AS bloque, b.paso, b.ubicacion AS ubic_bloque,
           (SELECT COUNT(*) FROM placa p WHERE p.bloque_id = b.id AND p.tecnica = 'HE') AS he,
           (SELECT COUNT(*) FROM placa p WHERE p.bloque_id = b.id) AS placas,
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
        return "Decalcificación"
    return fila["paso"]


def _ubicacion(fila):
    if pd.isna(fila["fecha_sacrificio"]):
        return "Bioterio (vivo)"
    if pd.isna(fila["bloque"]):
        return "En EDTA (manejo)"
    return fila["ubic_bloque"]


def ratones(busqueda="", paso="Todos"):
    df = _q(_RATONES + " ORDER BY s.id")
    df["paso_actual"] = df.apply(_paso, axis=1)
    df["donde"] = df.apply(_ubicacion, axis=1)
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


# ---------------- Placas ----------------
def placas(sid):
    df = _q("""
        SELECT p.id, p.serie, p.correlativo, p.tipo_portaobjeto, p.protocolo, p.destino,
               p.tecnica, p.fecha_corte, p.fecha_tecnica, p.rotulo, p.estado, p.ubicacion,
               r.estado_final AS resultado, r.comentario, u.nombre AS quien
        FROM placa p JOIN bloque b ON b.id = p.bloque_id
        LEFT JOIN resultado_placa r ON r.placa_id = p.id
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
        SELECT b.sujeto_id AS "Ratón", p.protocolo AS "Protocolo",
               SUM(p.tipo_portaobjeto = 'cargado') AS "Cargadas disponibles",
               SUM(p.tipo_portaobjeto = 'normal') AS "Normales disponibles",
               MIN(p.ubicacion) AS "Ubicación"
        FROM placa p JOIN bloque b ON b.id = p.bloque_id
        WHERE p.serie = 'set' AND p.tecnica IS NULL AND b.paso = 'Placas en técnicas'
        GROUP BY b.sujeto_id ORDER BY b.sujeto_id""")


def resultados_recientes():
    return _q("""
        SELECT r.fecha AS "Fecha", b.sujeto_id AS "Ratón", p.correlativo AS "Placa",
               r.tecnica_realizada AS "Técnica", r.estado_final AS "Resultado",
               r.comentario AS "Comentario", u.nombre AS "Quién"
        FROM resultado_placa r JOIN placa p ON p.id = r.placa_id
        JOIN bloque b ON b.id = p.bloque_id LEFT JOIN usuario u ON u.id = r.usuario_id
        ORDER BY r.fecha DESC""")


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
