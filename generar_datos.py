"""Crea la base de datos local (SQLite) con 30 ratones FICTICIOS.

Uso:  python3 generar_datos.py
Regenera todo desde cero (misma semilla = mismos datos). Los ratones "activos"
(vivos o en decalcificación) se fechan respecto de HOY para que se vean los avisos.

Reglas del laboratorio que imita:
- Cada ratón tiene dos defectos (izq./der.), con el mismo contenido o mezclado.
- Manejo: cirugía -> experimentación -> sacrificio/formalina -> decalcificación en EDTA,
  con cambios de solución cada pocos días.
- Llega a histología como cubo de parafina (se reincluye) o como cabeza en EDTA.
- Desgaste: pares; se tiñe con HE la placa par; revisión SA tras cada ronda.
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
USUARIOS = [(1, "Javiera", "histologia"), (2, "Docente responsable", "docente"),
            (3, "Estudiante A", "estudiante"), (4, "Estudiante B", "estudiante"),
            (5, "Estudiante C", "estudiante")]
CONTENIDOS = ["vacío", "células 200.000", "andamio", "andamio + células 200.000"]
CAJAS = ["Caja de placas 1", "Caja de placas 2", "Caja de placas 3"]

# Paso de cada ratón (n = 1..30). El resto: "Placas en técnicas".
PLAN = {1: "vivo", 2: "vivo", 3: "decalcificando", 4: "decalcificando", 5: "decalcificando",
        6: "Recepción", 7: "Reinclusión", 12: "Desgaste", 8: "Corte de set", 13: "Corte de set",
        9: "Tinción HE", 14: "Tinción HE", 11: "Archivado", 29: "Archivado",
        10: "Esperando revisión SA", 15: "Esperando revisión SA", 20: "Esperando revisión SA",
        25: "Esperando revisión SA", 30: "Esperando revisión SA"}
# Días desde el último cambio de EDTA para los que están decalcificando (3 y 5 => aviso).
ULTIMO_CAMBIO = {3: 5, 4: 1, 5: 4}


def iso(d):
    return d.isoformat() if d else None


def dmy(d):
    return d.strftime("%d/%m/%y")


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

    for n, num in enumerate(random.sample(range(9000000, 9999999), 30), start=1):
        sid, plan = str(num), PLAN.get(n, "Placas en técnicas")
        est = random.choice([3, 4, 5])
        caja = random.choice(CAJAS)
        semanas = random.choice([4, 8, 12])
        izq = random.choice(CONTENIDOS)
        der = izq if random.random() < 0.6 else random.choice(CONTENIDOS)

        # ---------- Manejo: fechas ----------
        if plan == "vivo":
            cirugia = HOY - timedelta(days=random.randint(5, 20))
            sacrificio = None
        elif plan == "decalcificando":
            ultimo = ULTIMO_CAMBIO[n]
            # inicio tal que el último cambio fue hace `ultimo` días
            sacrificio = HOY - timedelta(days=ultimo + 3 * random.randint(2, 5) + 2)
            cirugia = sacrificio - timedelta(weeks=semanas)
        else:
            cirugia = date(2025, 3, 1) + timedelta(days=random.randint(0, 120))
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
                 comentarios="Datos ficticios para prototipo")
        evento(con, 2, "sujeto", sid, "Cirugía: defectos bilaterales", cirugia, f"izq.: {izq} / der.: {der}")
        if plan == "vivo":
            continue
        evento(con, 2, "sujeto", sid, "Sacrificio y fijación en formalina", sacrificio)

        f_ct = sacrificio + timedelta(days=2)
        insertar(con, "estudio_imagen", sujeto_id=sid, tipo="microCT",
                 lugar="Centro de imagen (ficticio)", fecha=iso(f_ct))
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
            continue

        # ---------- Llega a histología ----------
        ini = f_ct + timedelta(days=2)
        en_edta = plan == "Recepción" or random.random() < 0.3
        if plan == "Recepción":
            ini = HOY - timedelta(days=30)
            fin = None
        else:
            fin = ini + timedelta(days=random.randint(21, 35))
        decalcificar(con, sid, ini, fin, est)
        forma = "cabeza en EDTA" if en_edta else "cubo de parafina"
        f_rec = (HOY - timedelta(days=1)) if plan in ("Recepción", "Reinclusión") else (fin + timedelta(days=random.randint(2, 6)))
        if not en_edta:
            f_incl = f_rec - timedelta(days=1)
            insertar(con, "procesamiento_previo", sujeto_id=sid, tipo="Inclusión previa",
                     fecha=iso(f_incl), lugar="Laboratorio externo", usuario_id=est)
            evento(con, est, "sujeto", sid, "Inclusión previa (laboratorio externo)", f_incl)

        bid = f"{sid}-B1"
        paso = plan
        insertar(con, "bloque", id=bid, sujeto_id=sid, forma_llegada=forma, fecha_recepcion=iso(f_rec),
                 paso=paso, estado="en lab",
                 ubicacion="Archivo histología" if paso == "Archivado" else
                           ("Frasco EDTA, mesón histología" if paso == "Recepción" else "Gaveta de bloques"))
        evento(con, 1, "bloque", bid, f"Recepción en histología ({forma})", f_rec)
        if paso in ("Recepción", "Reinclusión"):
            continue
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
                        placa(con, bid, "desgaste", corr, "normal", "evaluación", "HE", fecha, caja,
                              "HE", f_he, rotulo(sid, "HE", f_he, corr), "terminada")
                    else:
                        placa(con, bid, "desgaste", corr, "normal", "evaluación", "HE", fecha, caja)
            evento(con, 1, "bloque", bid, f"Desgaste ronda {ronda}: corte de par y HE", fecha)
            f_rev = fecha + timedelta(days=random.randint(3, 10))
            if paso == "Esperando revisión SA" and ronda == rondas:
                break
            ultima = ronda == rondas
            if paso == "Desgaste" and ultima:
                evento(con, 2, "bloque", bid, "Revisión SA", f_rev, "Profundizar desgaste")
                break
            evento(con, 2, "bloque", bid, "Revisión SA", f_rev,
                   "Indicar set de corte" if ultima else "Profundizar desgaste")
            fecha = f_rev + timedelta(days=2)
        if paso in ("Esperando revisión SA", "Desgaste", "Corte de set"):
            continue

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
                        placa(con, bid, "set", corr, "normal", protocolo, "HE", f_set, caja,
                              "HE", f_he, rotulo(sid, "HE", f_he, corr), "terminada")
                    else:
                        placa(con, bid, "set", corr, "normal", protocolo, "HE", f_set, caja)
                    continue
                if tenir and random.random() < 0.18:
                    e = random.choice([3, 4, 5])
                    f_tec = f_set + timedelta(days=random.randint(10, 40))
                    tec = random.choice(["IHQ/IF CD31", "IHQ/IF osteocalcina", "IHQ/IF Runx2",
                                         "IHQ/IF CD31", "Otra: tinción especial"])
                    final, coment = random.choice([
                        ("realizada", ""), ("realizada", "Buena señal en el borde del defecto."),
                        ("realizada con observaciones", "Fondo alto, interpretar con cuidado."),
                        ("en proceso", "Anticuerpo primario incubando."),
                        ("repetir", "Sin señal en control positivo."),
                        ("perdida", "Corte se desprendió en recuperación antigénica."),
                    ])
                    estado = {"perdida": "perdida", "en proceso": "en técnica"}.get(final, "terminada")
                    ubic = "Perdida" if final == "perdida" else f"Con {USUARIOS[e - 1][1]}"
                    pid = placa(con, bid, "set", corr, "cargado", protocolo, "IHQ/IF", f_set, ubic,
                                tec, f_tec, rotulo(sid, tec, f_tec, corr), estado)
                    insertar(con, "resultado_placa", placa_id=pid, usuario_id=e, tecnica_realizada=tec,
                             estado_final=final, comentario=coment, fecha=iso(f_tec))
                    evento(con, e, "placa", pid, f"Técnica: {tec}", f_tec, f"{final}. {coment}".strip())
                else:
                    placa(con, bid, "set", corr, "cargado", protocolo, "IHQ/IF", f_set, caja)
        if tenir:
            evento(con, 1, "bloque", bid, f"Tinción HE placas {sorted(he_tenidas)}", f_he)

    con.commit()
    for t in ["sujeto", "bloque", "placa", "resultado_placa", "cambio_edta", "evento"]:
        print(f"{t:16} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
    print(con.execute("SELECT paso, COUNT(*) FROM bloque GROUP BY paso").fetchall())
    con.close()


if __name__ == "__main__":
    main()
