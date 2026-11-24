"""Aplicación web (FastAPI): pantallas HTML con diseño propio.

Toda la lógica y las reglas de permisos están en servicios.py (capa intermedia).
Este archivo solo recibe pedidos, llama a servicios.py y muestra plantillas.

Ejecutar en local:   uvicorn web.main:app --reload
"""
import os
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

from typing import List

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
# En local, la conexión a Supabase puede venir de .streamlit/secrets.toml o de un archivo .env
for archivo in (RAIZ / ".streamlit" / "secrets.toml", RAIZ / ".env"):
    if archivo.exists() and "DATABASE_URL" not in os.environ:
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            if linea.strip().startswith("DATABASE_URL"):
                os.environ["DATABASE_URL"] = linea.split("=", 1)[1].strip().strip('"').strip("'")

import servicios as sv  # noqa: E402

AQUI = Path(__file__).parent
app = FastAPI(title="OsteoTraza")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "solo-para-desarrollo-local"),
                   max_age=60 * 60 * 12, same_site="lax")
app.mount("/static", StaticFiles(directory=AQUI / "static"), name="static")
plantillas = Jinja2Templates(directory=AQUI / "templates")
plantillas.env.filters["url"] = lambda s: quote(str(s), safe="")

COLOR_PASO = {
    "En experimentación": "lila", "Fijación en formalina": "lila", "Decalcificación": "ambar", "Recepción": "azul", "Reinclusión": "azul",
    "Desgaste": "azul", "Esperando revisión": "naranja", "Corte de set": "azul", "Tinción HE": "azul",
    "Placas en técnicas": "verde", "Archivado": "gris",
}


# ---------------------------------------------------------------- utilidades
def usuario(request):
    return request.session.get("usuario")


def avisar(request, texto, tipo="ok"):
    request.session["mensaje"] = {"texto": texto, "tipo": tipo}


def volver(url):
    return RedirectResponse(url, status_code=303)


SECCIONES = {"inicio", "manejo", "histologia", "tecnicas", "ubicaciones", "ratones"}


def pagina(request, plantilla, activo="", **datos):
    alertas = sv.alertas_edta()
    u = usuario(request)
    pend = sv.alertas_histologia()
    n_histo = (len(pend["revision"]) if u["rol"] in ("docente", "admin") else 0) + \
              (len(pend["corte"]) if sv.puede(u, "paso_histologia") else 0)
    contexto = {
        "u": usuario(request), "rol": sv.NOMBRE_ROL.get(usuario(request)["rol"], ""),
        "mensaje": request.session.pop("mensaje", None), "activo": activo,
        "n_alertas": int(alertas["toca_cambio"].sum()) if not alertas.empty and sv.puede(u, "cambio_edta") else 0,
        "n_histo": n_histo, "pendientes": pend,
        "nube": sv.ES_POSTGRES, "color_paso": COLOR_PASO, "puede": lambda a: sv.puede(usuario(request), a),
        "hoy": date.today().isoformat(), "dias_edta": sv.DIAS_CAMBIO_EDTA,
    }
    contexto.update(datos)
    return plantillas.TemplateResponse(request, plantilla, contexto)


def protegido(funcion):
    """Exige haber ingresado; si no, manda al login."""
    from functools import wraps

    @wraps(funcion)
    async def envoltorio(request: Request, *args, **kwargs):
        if not usuario(request):
            return volver("/login")
        return await funcion(request, *args, **kwargs)
    return envoltorio


def ejecutar(request, funcion, *args, ok="Guardado"):
    try:
        funcion(usuario(request), *args)
        avisar(request, ok)
    except (PermissionError, ValueError) as e:
        avisar(request, str(e), "error")


def a_fecha(texto):
    return date.fromisoformat(texto) if texto else date.today()


def tipo_placa(p):
    """Clase visual de una placa según técnica y resultado."""
    if p.get("estado") == "inutilizable":
        return "perdida"
    if p.get("tecnica") == "HE":
        return "he"
    if p.get("tecnica"):
        return {"en proceso": "proceso", "repetir": "repetir"}.get(p.get("resultado"), "hecha")
    return "cargada" if p.get("tipo_portaobjeto") == "cargado" else "normal"


plantillas.env.globals["tipo_placa"] = tipo_placa


# ---------------------------------------------------------------- ingreso
@app.get("/login", response_class=HTMLResponse)
async def ver_login(request: Request):
    return plantillas.TemplateResponse(request, "login.html", {
        "usuarios": sv.usuarios_login(), "mensaje": request.session.pop("mensaje", None)})


@app.post("/login")
async def ingresar(request: Request, nombre: str = Form(...), clave: str = Form(...)):
    u = sv.autenticar(nombre, clave)
    if not u:
        avisar(request, "Contraseña incorrecta.", "error")
        return volver("/login")
    request.session["usuario"] = u
    return volver("/")


@app.get("/salir")
async def salir(request: Request):
    request.session.clear()
    return volver("/login")


# ---------------------------------------------------------------- inicio
@app.get("/", response_class=HTMLResponse)
@protegido
async def inicio(request: Request):
    al = sv.alertas_edta()
    pend = sv.alertas_histologia()
    u = usuario(request)
    return pagina(request, "inicio.html", "inicio",
                  revisar=pend["revision"] if u["rol"] in ("docente", "admin") else [],
                  cortar=pend["corte"] if sv.puede(u, "paso_histologia") else [],
                  alertas=al[al["toca_cambio"]].to_dict("records") if not al.empty and sv.puede(u, "cambio_edta") else [],
                  conteo=sv.conteo_por_paso(), pasos=sv.PASOS,
                  eventos=sv.eventos_recientes(12).to_dict("records"))


@app.get("/buscar", response_class=HTMLResponse)
@protegido
async def buscar(request: Request, q: str = ""):
    r, p = sv.buscar(q) if q.strip() else (None, None)
    if r is not None and len(r) == 1 and (p is None or p.empty):
        return volver(f"/ratones/{r['id'].iloc[0]}")
    return pagina(request, "buscar.html", "", q=q,
                  ratones=[] if r is None else r["id"].tolist(),
                  placas=[] if p is None else p.to_dict("records"))


# ---------------------------------------------------------------- ratones
@app.get("/ratones", response_class=HTMLResponse)
@protegido
async def lista_ratones(request: Request, paso: str = "Todos", q: str = "", orden: str = "Número"):
    df = sv.ratones(q, paso, orden)
    return pagina(request, "ratones.html", "ratones", ratones=df.to_dict("records"),
                  pasos=sv.PASOS, paso=paso, q=q, conteo=sv.conteo_por_paso(),
                  orden=orden, ordenes=list(sv.ORDENES))


def _datos_form(form):
    return {k: (form.get(k) or "").strip() for k in sv.CAMPOS_RATON}


@app.get("/ratones/nuevo", response_class=HTMLResponse)
@protegido
async def nuevo_raton(request: Request):
    return pagina(request, "raton_form.html", "ratones", d={}, sid="", nuevo=True, contenidos=sv.CONTENIDOS)


@app.post("/ratones/nuevo")
@protegido
async def crear_raton(request: Request):
    form = await request.form()
    sid = (form.get("id") or "").strip()
    try:
        sv.ingresar_raton(usuario(request), sid, _datos_form(form))
        avisar(request, f"Ratón {sid} ingresado")
        return volver(f"/ratones/{sid}")
    except (PermissionError, ValueError) as e:
        avisar(request, str(e), "error")
        return volver("/ratones/nuevo")


@app.get("/ratones/{sid}/editar", response_class=HTMLResponse)
@protegido
async def ver_editar_raton(request: Request, sid: str):
    r = sv.raton(sid)
    if not r:
        return volver("/ratones")
    return pagina(request, "raton_form.html", "ratones", d=r["datos"], sid=sid, nuevo=False, contenidos=sv.CONTENIDOS)


@app.post("/ratones/{sid}/editar")
@protegido
async def guardar_raton(request: Request, sid: str):
    form = await request.form()
    ejecutar(request, sv.editar_raton, sid, _datos_form(form), ok="Datos del ratón guardados")
    return volver(f"/ratones/{sid}")


@app.post("/histologia/lote")
@protegido
async def lote_histologia(request: Request, accion: str = Form(...), sids: List[str] = Form([]),
                          fecha: str = Form("")):
    f = a_fecha(fecha)
    funcion = {"inclusion": sv.registrar_inclusion, "he": sv.tenir_he_set}.get(accion)
    if not funcion or not sids:
        avisar(request, "Marca al menos un ratón.", "error")
        return volver("/histologia")
    ok, errores = 0, []
    for sid in sids:
        try:
            funcion(usuario(request), f"{sid}-B1", f)
            ok += 1
        except (PermissionError, ValueError) as e:
            errores.append(f"{sid}: {e}")
    avisar(request, f"{ok} registrado(s)." + (" Errores: " + "; ".join(errores) if errores else ""),
           "error" if errores else "ok")
    return volver("/histologia")


@app.get("/ratones/{sid}", response_class=HTMLResponse)
@protegido
async def ficha(request: Request, sid: str, tab: str = "resumen", desde: str = "ratones"):
    r = sv.raton(sid)
    if not r:
        avisar(request, f"No existe el ratón {sid}.", "error")
        return volver("/ratones")
    dec, cambios = sv.decalcificacion(sid)
    al = sv.alertas_edta()
    fila_al = al[al["id"] == sid].to_dict("records") if not al.empty else []
    ps = sv.placas(sid)
    desde = desde if desde in SECCIONES else "ratones"
    return pagina(request, "raton.html", desde, desde=desde, r=r, d=r["datos"], b=r["bloque_info"], tab=tab,
                  siguiente=sv.SIGUIENTE.get(r["paso_actual"]), linaje=sv.linaje(sid),
                  placas=ps.to_dict("records"), dec=dec, cambios=cambios.to_dict("records"),
                  edta=fila_al[0] if fila_al else None, img=sv.imagenologia(sid).to_dict("records"),
                  previo=sv.procesamiento_previo(sid).to_dict("records"),
                  historial=sv.historial(sid).to_dict("records"),
                  protocolos=list(sv.PROTOCOLOS), labs=sv.LABS,
                  n_he=sum(1 for p in ps.to_dict("records") if p["tecnica"] == "HE"))


@app.post("/ratones/{sid}/registrar")
@protegido
async def registrar(request: Request, sid: str, accion: str = Form(...), fecha: str = Form(""),
                    forma: str = Form(""), decision: str = Form(""), protocolo: str = Form(""),
                    ubicacion: str = Form(""), n_placas: int = Form(2), tenir: List[int] = Form([])):
    f = a_fecha(fecha)
    bid = f"{sid}-B1"
    acciones = {
        "sacrificio": (sv.registrar_sacrificio, (sid, f), "Sacrificio y fijación en formalina registrados"),
        "iniciar_decal": (sv.iniciar_decalcificacion, (sid, f), "Inicio de decalcificación registrado"),
        "edta": (sv.registrar_cambio_edta, (sid, f), "Cambio de EDTA registrado"),
        "enviar": (sv.enviar_a_histologia, (sid, f, forma), "Recepción en histología registrada"),
        "inclusion": (sv.registrar_inclusion, (bid, f), "Inclusión registrada"),
        "desgaste": (sv.cortar_desgaste, (bid, f, n_placas), f"{n_placas} placa(s) de desgaste registradas"),
        "tenir_desgaste": (sv.tenir_desgaste, (bid, f, tenir), "Tinción HE del desgaste registrada"),
        "revision": (sv.registrar_revision_sa, (bid, f, decision, protocolo), "Revisión registrada"),
        "set": (sv.cortar_set, (bid, f, protocolo), "Set de corte registrado"),
        "he": (sv.tenir_he_set, (bid, f), "Tinción HE registrada"),
        "archivar": (sv.archivar, (bid, f), "Bloque archivado"),
        "mover_bloque": (sv.mover_bloque, (bid, ubicacion, f), "Ubicación del bloque actualizada"),
    }
    if accion not in acciones:
        avisar(request, "Acción desconocida.", "error")
    else:
        funcion, args, ok = acciones[accion]
        ejecutar(request, funcion, *args, ok=ok)
    destino = request.headers.get("referer") or f"/ratones/{sid}"
    return volver(destino)


# ---------------------------------------------------------------- placas
@app.get("/placas/{pid}", response_class=HTMLResponse)
@protegido
async def ver_placa(request: Request, pid: int):
    p = sv.placa(pid)
    if not p:
        avisar(request, "Placa no encontrada.", "error")
        return volver("/ratones")
    return pagina(request, "placa.html", "ratones", p=p,
                  movimientos=sv.movimientos_placa(pid).to_dict("records"),
                  hermanas=sv.placas(p["sujeto_id"]).to_dict("records"),
                  resultados=sv.RESULTADOS, labs=sv.LABS)


@app.post("/placas/{pid}/tecnica")
@protegido
async def tecnica(request: Request, pid: int, tipo: str = Form(...), detalle: str = Form(""),
                  resultado: str = Form(...), comentario: str = Form(""), fecha: str = Form("")):
    tec = f"IHQ/IF {detalle}".strip() if tipo == "IHQ/IF" else f"Otra: {detalle}".strip()
    ejecutar(request, sv.registrar_tecnica, pid, a_fecha(fecha), tec, resultado, comentario,
             ok="Técnica registrada")
    return volver(f"/placas/{pid}")


@app.post("/placas/{pid}/inutilizable")
@protegido
async def inutilizable(request: Request, pid: int, comentario: str = Form(""), fecha: str = Form("")):
    ejecutar(request, sv.marcar_inutilizable, pid, a_fecha(fecha), comentario, ok="Placa marcada como inutilizable")
    return volver(f"/placas/{pid}")


@app.post("/placas/{pid}/mover")
@protegido
async def mover(request: Request, pid: int, destino: str = Form("")):
    ejecutar(request, sv.mover_placa, pid, destino, date.today(), ok="Ubicación actualizada")
    return volver(f"/placas/{pid}")


# ---------------------------------------------------------------- secciones
@app.get("/manejo", response_class=HTMLResponse)
@protegido
async def manejo(request: Request):
    df = sv.ratones()
    al = sv.alertas_edta()
    dias = dict(zip(al["id"], al["dias"])) if not al.empty else {}
    return pagina(request, "manejo.html", "manejo",
                  vivos=df[df["paso_actual"] == "En experimentación"].to_dict("records"),
                  formalina=df[df["paso_actual"] == "Fijación en formalina"].to_dict("records"),
                  edta=[dict(f, dias=int(dias[f["id"]])) for f in df.to_dict("records") if f["id"] in dias])


@app.get("/histologia", response_class=HTMLResponse)
@protegido
async def histologia(request: Request):
    df = sv.ratones()
    grupos = [(p, df[df["paso_actual"] == p].to_dict("records")) for p in sv.PASOS_HISTO]
    return pagina(request, "histologia.html", "histologia", grupos=grupos)


@app.get("/tecnicas", response_class=HTMLResponse)
@protegido
async def tecnicas(request: Request, resultado: str = "Todos"):
    return pagina(request, "tecnicas.html", "tecnicas",
                  disponibles=sv.placas_para_tecnicas().to_dict("records"),
                  resultados=sv.resultados_recientes(resultado).to_dict("records"),
                  filtro=resultado, opciones=sv.RESULTADOS + ["inutilizable"])


@app.get("/ubicaciones", response_class=HTMLResponse)
@protegido
async def ubicaciones(request: Request, lab: str = ""):
    bloques, placas_ = sv.en_ubicacion(lab) if lab else (None, None)
    bio = sv.ratones_en_bioterio().to_dict("records") if lab == "Bioterio" else []
    return pagina(request, "ubicaciones.html", "ubicaciones", arbol=sv.arbol_ubicaciones(), sel=lab,
                  labs=sv.LABS, bioterio=bio,
                  bloques=[] if bloques is None else bloques.to_dict("records"),
                  placas=[] if placas_ is None else placas_.to_dict("records"))


@app.post("/edta/{sid}")
@protegido
async def edta_rapido(request: Request, sid: str):
    ejecutar(request, sv.registrar_cambio_edta, sid, date.today(), ok=f"Cambio de EDTA registrado ({sid})")
    return volver(request.headers.get("referer") or "/")


@app.post("/ubicaciones/mover")
@protegido
async def mover_varios(request: Request, destino: str = Form(...), placas: List[int] = Form([]),
                       bloques: List[str] = Form([])):
    n = len(placas) + len(bloques)
    ejecutar(request, sv.mover_varios, placas, bloques, destino, date.today(),
             ok=f"{n} muestra(s) movida(s) a {destino}")
    return volver(request.headers.get("referer") or "/ubicaciones")
