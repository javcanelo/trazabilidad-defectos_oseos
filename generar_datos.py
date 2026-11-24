"""Crea la base de datos local (SQLite) con 15 ratones FICTICIOS.

Uso:  python3 generar_datos.py
Regenera todo desde cero (misma semilla = mismos datos). Las fechas de cada ratón
se desplazan para que su último registro sea reciente (días o pocas semanas atrás).

Reglas del laboratorio que imita:
- Cada ratón tiene dos defectos (izq./der.), con el mismo contenido o mezclado.
- Manejo: cirugía -> experimentación -> sacrificio/formalina -> decalcificación en EDTA,
  con cambios de solución cada pocos días.
- Llega a histología como cubo de parafina (se reincluye) o como cabeza en EDTA.
- Desgaste: pares; se tiñe con HE la placa par; revisión tras cada ronda.
- Set de corte: correlativo vuelve a 1. HE en portaobjeto normal, IHQ/IF en cargado.
- El rótulo nace al hacer la técnica: número | técnica | dd/mm/aa | correlativo.
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "data" / "prototipo.db"
HOY = date.today()
random.seed(24)

PROTOCOLOS = {
    "estándar": ([("HE", 3), ("IHQ/IF", 3), ("HE", 3), ("IHQ/IF", 3), ("HE", 3)], {1, 8, 15}),
    "estrella": ([("IHQ/IF", 4), ("HE", 4)] * 2 + [("IHQ/IF", 4), ("HE", 3)], {5, 21}),
    "corazón": ([("IHQ/IF", 4), ("HE", 4)] * 4 + [("IHQ/IF", 4), ("HE", 3)], {5, 21, 39}),
}
USUARIOS = [(1, "TM", "tm"), (2, "Docente", "docente"),
            (3, "Estudiante", "estudiante"), (6, "Admin", "admin")]
CONTENIDOS = ["vacío", "células 200.000", "andamio", "andamio + células 200.000"]
CAJAS = ["Lab. A"]  # ya no se usan cajas: solo el laboratorio


def up(caja):
    """Las placas se registran solo por laboratorio."""
    return "Lab. A"

# Paso de cada ratón (n = 1..15).
PLAN = {1: "vivo", 2: "vivo", 3: "decalcificando", 4: "decalcificando",
        5: "Recepción", 6: "Reinclusión", 7: "Desgaste",
        8: "Esperando revisión", 9: "Esperando revisión", 10: "Corte de set",
        11: "Tinción HE", 12: "Placas en técnicas", 13: "Placas en técnicas", 14: "Archivado",
        15: "formalina"}
N_RATONES = len(PLAN)
# Días desde el último cambio de EDTA para los que están decalcificando (5 => aviso).
ULTIMO_CAMBIO = {3: 5, 4: 1}
# Hace cuántos días fue el último registro de cada ratón (los más avanzados, hace más).
HACE = {"Recepción": (1, 3), "Reinclusión": (1, 4), "Desgaste": (2, 6),
        "Esperando revisión": (1, 7), "Corte de set": (1, 5), "Tinción HE": (1, 4),
        "Placas en técnicas": (2, 12), "Archivado": (20, 45)}
SHIFT = timedelta(0)   # desplazamiento de fechas del ratón en curso
MAXF = [None]          # fecha más tardía escrita (para calcular el desplazamiento)


def _mover(d):
    d = d + SHIFT
    if MAXF[0] is None or d > MAXF[0]:
        MAXF[0] = d
    return d


def iso(d):
    return _mover(d).isoformat() if d else None


def dmy(d):
    return _mover(d).strftime("%d/%m/%y")


def rotulo(num, tecnica, fecha, corr):
    return f"{num} | {tecnica} | {dmy(fecha)} | {corr}"


def insertar(con, tabla, **campos):
    cols = ", ".join(campos)
    marcas = ", ".join("?" for _ in campos)
    return con.execute(f"INSERT INTO {tabla} ({cols}) VALUES ({marcas})",
                       tuple(campos.values())).lastrowid


def evento(con, usuario, entidad, entidad_id, accion, fecha, detalle=""):
    insertar(con, "evento", usuario_id=usuario, entidad=entidad, entidad_id=str(entidad_id),
             accion=accion, fecha=iso(fecha), detalle=detalle)


def placa(con, bloque, serie, corr, porta, protocolo, destino, f_corte, ubic,
          tecnica=None, f_tec=None, rot=None, estado="disponible"):
    return insertar(con, "placa", bloque_id=bloque, serie=serie, correlativo=corr,
                    tipo_portaobjeto=porta, protocolo=protocolo, destino=destino, tecnica=tecnica,
                    fecha_corte=iso(f_corte), fecha_tecnica=iso(f_tec), rotulo=rot,
                    ubicacion=ubic, estado=estado)


def reiniciar(con):
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        con.execute(f"DROP TABLE IF EXISTS {t}")
    con.executescript((BASE / "esquema.sql").read_text(encoding="utf-8"))


def decalcificar(con, sid, inicio, fin, est):
    """Registra la decalcificación y un cambio de EDTA cada 3–4 días."""
    insertar(con, "decalcificacion", sujeto_id=sid, fecha_inicio=iso(inicio), fecha_fin=iso(fin))
    evento(con, est, "sujeto", sid, "Inicio decalcificación EDTA", inicio)
    hasta = fin or HOY
    f = inicio + timedelta(days=random.randint(3, 4))
    while f <= hasta:
        insertar(con, "cambio_edta", sujeto_id=sid, fecha=iso(f), usuario_id=est)
        evento(con, est, "sujeto", sid, "Cambio de EDTA", f)
        f += timedelta(days=random.randint(3, 4))
    if fin:
        evento(con, est, "sujeto", sid, "Fin decalcificación", fin)


def main():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    reiniciar(con)
    from servicios import cifrar  # misma función que usa el login
    for uid, nombre, rol in USUARIOS:
        insertar(con, "usuario", id=uid, nombre=nombre, rol=rol, clave_hash=cifrar("demo123", uid))

    global SHIFT
    prueba = sqlite3.connect(":memory:")
    prueba.executescript((BASE / "esquema.sql").read_text(encoding="utf-8"))
    for n, num in enumerate(random.sample(range(9000000, 9999999), N_RATONES), start=1):
        plan = PLAN[n]
        if plan in ("vivo", "decalcificando", "formalina"):   # ya fechados respecto de HOY
            SHIFT = timedelta(0)
            raton(con, n, num)
            continue
        # 1) ensayo sin desplazar para saber la última fecha; 2) se repite desplazado
        estado_azar, MAXF[0], SHIFT = random.getstate(), None, timedelta(0)
        raton(prueba, n, num)
        objetivo = HOY - timedelta(days=random.randint(*HACE[plan]))
        SHIFT = objetivo - MAXF[0]
        siguiente = random.getstate()
        random.setstate(estado_azar)
        raton(con, n, num)
        random.setstate(siguiente)
        SHIFT = timedelta(0)

    con.commit()
    for t in ["sujeto", "bloque", "placa", "resultado_placa", "cambio_edta", "evento"]:
        print(f"{t:16} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
    print(con.execute("SELECT paso, COUNT(*) FROM bloque GROUP BY paso").fetchall())
    con.close()


def raton(con, n, num):
    if True:
        sid, plan = str(num), PLAN[n]
        est = 3
        caja = random.choice(CAJAS)
        semanas = random.choice([4, 8, 12])
        izq = random.choice(CONTENIDOS)
        der = izq if random.random() < 0.6 else random.choice(CONTENIDOS)

        # ---------- Manejo: fechas ----------
        if plan == "vivo":
            cirugia = HOY - timedelta(days=random.randint(5, 20))
            sacrificio = None
        elif plan == "formalina":
            sacrificio = HOY - timedelta(days=1)
            cirugia = sacrificio - timedelta(weeks=semanas)
        elif plan == "decalcificando":
            ultimo = ULTIMO_CAMBIO[n]
            # inicio tal que el último cambio fue hace `ultimo` días
            sacrificio = HOY - timedelta(days=ultimo + 3 * random.randint(2, 5) + 2)
            cirugia = sacrificio - timedelta(weeks=semanas)
        else:
            cirugia = date(2026, 1, 1)  # se desplaza después
            sacrificio = cirugia + timedelta(weeks=semanas)
        nacimiento = cirugia - timedelta(weeks=random.choice([8, 10, 12]))

        insertar(con, "sujeto", id=sid, caja=str(random.randint(1, 8)),
                 sexo=random.choice(["Hembra", "Macho"]), fecha_nacimiento=iso(nacimiento),
                 fecha_cirugia=iso(cirugia), fecha_sacrificio=iso(sacrificio),
                 contenido_defecto_izq=izq, contenido_defecto_der=der,
                 tiempo_experimentacion=f"{semanas} semanas", anestesia="0,10 ml",
                 experimento="Defecto calvarial bilateral",
                 grupo="control" if izq == der == "vacío" else "experimental",
                 lista=random.choice(["", "", "corazón", "estándar"]),
                 tesis_responsable=random.choice(["Tesis A", "Tesis B"]), ct_texto="",
                 comentarios=None)
        evento(con, 2, "sujeto", sid, "Cirugía: defectos bilaterales", cirugia, f"izq.: {izq} / der.: {der}")
        if plan == "vivo":
            return
        evento(con, 2, "sujeto", sid, "Sacrificio y fijación en formalina", sacrificio)
        if plan == "formalina":
            return

        f_ct = sacrificio + timedelta(days=2)
        insertar(con, "estudio_imagen", sujeto_id=sid, tipo="microCT",
                 lugar="Centro de imagen (ficticio)", fecha=iso(f_ct),
                 vista_previa="/static/microct_ejemplo.png")
        evento(con, 2, "sujeto", sid, "MicroCT", f_ct)

        if plan == "decalcificando":
            ini = sacrificio + timedelta(days=2)
            insertar(con, "decalcificacion", sujeto_id=sid, fecha_inicio=iso(ini), fecha_fin=None)
            evento(con, est, "sujeto", sid, "Inicio decalcificación EDTA", ini)
            f = ini + timedelta(days=3)
            ultimo = HOY - timedelta(days=ULTIMO_CAMBIO[n])
            while f < ultimo:
                insertar(con, "cambio_edta", sujeto_id=sid, fecha=iso(f), usuario_id=est)
                evento(con, est, "sujeto", sid, "Cambio de EDTA", f)
                f += timedelta(days=3)
            insertar(con, "cambio_edta", sujeto_id=sid, fecha=iso(ultimo), usuario_id=est)
            evento(con, est, "sujeto", sid, "Cambio de EDTA", ultimo)
            return

        # ---------- Llega a histología ----------
        ini = f_ct + timedelta(days=2)
        en_edta = plan == "Recepción" or random.random() < 0.3
        fin = ini + timedelta(days=random.randint(21, 35))
        decalcificar(con, sid, ini, fin, est)
        forma = "cabeza en EDTA" if en_edta else "cubo de parafina"
        f_rec = fin + timedelta(days=random.randint(2, 6))
        if not en_edta:
            f_incl = f_rec - timedelta(days=1)
            insertar(con, "procesamiento_previo", sujeto_id=sid, tipo="Inclusión previa",
                     fecha=iso(f_incl), lugar="Laboratorio externo", usuario_id=est)
            evento(con, est, "sujeto", sid, "Inclusión previa (laboratorio externo)", f_incl)

        bid = f"{sid}-B1"
        paso = plan
        insertar(con, "bloque", id=bid, sujeto_id=sid, forma_llegada=forma, fecha_recepcion=iso(f_rec),
                 paso=paso, estado="en lab",
                 ubicacion="Lab. A")
        evento(con, 1, "bloque", bid, f"Recepción en histología ({forma})", f_rec)
        if paso in ("Recepción", "Reinclusión"):
            return
        f_reincl = f_rec + timedelta(days=random.randint(2, 6))
        con.execute("UPDATE bloque SET fecha_reinclusion=? WHERE id=?", (iso(f_reincl), bid))
        evento(con, 1, "bloque", bid, "Inclusión en casete" if en_edta else "Reinclusión en casete", f_reincl)

        # ---------- Desgaste ----------
        rondas = random.choices([1, 2, 3], weights=[2, 6, 2])[0]
        fecha = f_reincl + timedelta(days=2)
        corr = 0
        for ronda in range(1, rondas + 1):
            for _ in range(2 if (ronda == 1 and random.random() < 0.3) else 1):
                for _ in range(2):
                    corr += 1
                    if corr % 2 == 0:
                        f_he = fecha + timedelta(days=1)
                        placa(con, bid, "desgaste", corr, "normal", "evaluación", "HE", fecha, up(caja),
                              "HE", f_he, rotulo(sid, "HE", f_he, corr), "terminada")
                    else:
                        placa(con, bid, "desgaste", corr, "normal", "evaluación", "HE", fecha, up(caja))
            evento(con, 1, "bloque", bid, f"Desgaste ronda {ronda}: corte de par y HE", fecha)
            f_rev = fecha + timedelta(days=random.randint(3, 10))
            if paso == "Esperando revisión" and ronda == rondas:
                break
            ultima = ronda == rondas
            if paso == "Desgaste" and ultima:
                evento(con, 2, "bloque", bid, "Revisión", f_rev, "Profundizar desgaste")
                break
            evento(con, 2, "bloque", bid, "Revisión", f_rev,
                   "Indicar set de corte" if ultima else "Profundizar desgaste")
            fecha = f_rev + timedelta(days=2)
        if paso in ("Esperando revisión", "Desgaste", "Corte de set"):
            return

        # ---------- Set de corte ----------
        protocolo = random.choice(list(PROTOCOLOS))
        grupos, he_tenidas = PROTOCOLOS[protocolo]
        f_set, f_he = fecha, fecha + timedelta(days=1)
        evento(con, 1, "bloque", bid, f"Corte set {protocolo}", f_set)
        tenir = paso != "Tinción HE"
        corr = 0
        for destino, cantidad in grupos:
            for _ in range(cantidad):
                corr += 1
                if destino == "HE":
                    if corr in he_tenidas and tenir:
                        placa(con, bid, "set", corr, "normal", protocolo, "HE", f_set, up(caja),
                              "HE", f_he, rotulo(sid, "HE", f_he, corr), "terminada")
                    else:
                        placa(con, bid, "set", corr, "normal", protocolo, "HE", f_set, up(caja))
                    continue
                if tenir and random.random() < 0.5:
                    e = 3
                    f_tec = f_set + timedelta(days=random.randint(10, 40))
                    tec = random.choice(["IHQ/IF CD31", "IHQ/IF osteocalcina", "IHQ/IF Runx2",
                                         "IHQ/IF CD31", "Otra: tinción especial"])
                    final, coment = random.choice([
                        ("realizada", ""), ("realizada", "Buena señal en el borde del defecto."),
                        ("realizada", "Marcaje claro en tejido neoformado."), ("realizada", ""),
                        ("realizada", "Control positivo y negativo correctos."),
                        ("realizada con observaciones", "Fondo alto, interpretar con cuidado."),
                        ("realizada con observaciones", "Señal débil pero específica."),
                        ("en proceso", "Anticuerpo primario incubando."),
                        ("repetir", "Sin señal en control positivo."),
                        ("inutilizable", "Corte desprendido o placa dañada."),
                    ])
                    estado = {"inutilizable": "inutilizable", "en proceso": "en técnica"}.get(final, "terminada")
                    ubic = "Lab. B"
                    if final == "inutilizable":
                        tec = None
                        pid = placa(con, bid, "set", corr, "cargado", protocolo, "IHQ/IF", f_set, "Lab. A",
                                    estado=estado)
                        insertar(con, "resultado_placa", placa_id=pid, usuario_id=e, tecnica_realizada=None,
                                 estado_final=final, comentario=coment, fecha=iso(f_tec))
                        evento(con, e, "placa", pid, "Placa inutilizable", f_tec, coment)
                        continue
                    pid = placa(con, bid, "set", corr, "cargado", protocolo, "IHQ/IF", f_set, ubic,
                                tec, f_tec, rotulo(sid, tec, f_tec, corr), estado)
                    insertar(con, "resultado_placa", placa_id=pid, usuario_id=e, tecnica_realizada=tec,
                             estado_final=final, comentario=coment, fecha=iso(f_tec))
                    evento(con, e, "placa", pid, f"Técnica: {tec}", f_tec, f"{final}. {coment}".strip())
                else:
                    placa(con, bid, "set", corr, "cargado", protocolo, "IHQ/IF", f_set, up(caja))
        if tenir:
            evento(con, 1, "bloque", bid, f"Tinción HE placas {sorted(he_tenidas)}", f_he)


if __name__ == "__main__":
    main()
