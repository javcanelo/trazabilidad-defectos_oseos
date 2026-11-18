"""Aplicación web (FastAPI): pantallas HTML con diseño propio.

Toda la lógica y las reglas de permisos están en servicios.py (capa intermedia).
Este archivo solo recibe pedidos, llama a servicios.py y muestra plantillas.

Ejecutar en local:   uvicorn web.main:app --reload
"""
import io
import os
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

import qrcode
import qrcode.image.svg
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
    "En experimentación": "lila", "Decalcificación": "ambar", "Recepción": "azul", "Reinclusión": "azul",
    "Desgaste": "azul", "Esperando revisión SA": "naranja", "Corte de set": "azul", "Tinción HE": "azul",
    "Placas en técnicas": "verde", "Archivado": "gris",
}


# ---------------------------------------------------------------- utilidades
def usuario(request):
    return request.session.get("usuario")


def avisar(request, texto, tipo="ok"):
    request.session["mensaje"] = {"texto": texto, "tipo": tipo}


def volver(url):
    return RedirectResponse(url, status_code=303)


def pagina(request, plantilla, activo="", **datos):
    alertas = sv.alertas_edta()
    contexto = {
        "u": usuario(request), "rol": sv.NOMBRE_ROL.get(usuario(request)["rol"], ""),
        "mensaje": request.session.pop("mensaje", None), "activo": activo,
        "n_alertas": int(alertas["toca_cambio"].sum()) if not alertas.empty else 0,
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


def qr_svg(texto):
    img = qrcode.make(texto, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=1)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode()


def tipo_placa(p):
    """Clase visual de una placa según técnica y resultado."""
    if p.get("tecnica") == "HE":
        return "he"
    if p.get("tecnica"):
        return {"perdida": "perdida", "en proceso": "proceso", "repetir": "repetir"}.get(p.get("resultado"), "hecha")
    return "cargada" if p.get("tipo_portaobjeto") == "cargado" else "normal"


plantillas.env.globals["tipo_placa"] = tipo_placa


# ---------------------------------------------------------------- ingreso
@app.get("/login", response_class=HTMLResponse)
async def ver_login(request: Request):
    return plantillas.TemplateResponse(request, "login.html", {
        "usuarios": sv.nombres_usuarios(), "mensaje": request.session.pop("mensaje", None)})


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
    return pagina(request, "inicio.html", "inicio",
                  alertas=al[al["toca_cambio"]].to_dict("records") if not al.empty else [],
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
async def lista_ratones(request: Request, paso: str = "Todos", q: str = ""):
    df = sv.ratones(q, paso)
    return pagina(request, "ratones.html", "ratones", ratones=df.to_dict("records"),
                  pasos=sv.PASOS, paso=paso, q=q, conteo=sv.conteo_por_paso())


@app.get("/ratones/{sid}", response_class=HTMLResponse)
@protegido
async def ficha(request: Request, sid: str, tab: str = "resumen"):
    r = sv.raton(sid)
    if not r:
        avisar(request, f"No existe el ratón {sid}.", "error")
        return volver("/ratones")
    dec, cambios = sv.decalcificacion(sid)
    al = sv.alertas_edta()
    fila_al = al[al["id"] == sid].to_dict("records") if not al.empty else []
    ps = sv.placas(sid)
    return pagina(request, "raton.html", "ratones", r=r, d=r["datos"], b=r["bloque_info"], tab=tab,
                  siguiente=sv.SIGUIENTE.get(r["paso_actual"]), linaje=sv.linaje(sid),
                  placas=ps.to_dict("records"), dec=dec, cambios=cambios.to_dict("records"),
                  edta=fila_al[0] if fila_al else None, img=sv.imagenologia(sid).to_dict("records"),
                  previo=sv.procesamiento_previo(sid).to_dict("records"),
                  historial=sv.historial(sid).to_dict("records"),
                  protocolos=list(sv.PROTOCOLOS), cajas=sv.cajas_placas(),
                  n_he=sum(1 for p in ps.to_dict("records") if p["tecnica"] == "HE"))


@app.post("/ratones/{sid}/registrar")
@protegido
async def registrar(request: Request, sid: str, accion: str = Form(...), fecha: str = Form(""),
                    forma: str = Form(""), decision: str = Form(""), protocolo: str = Form(""),
                    caja: str = Form(""), ubicacion: str = Form("")):
    f = a_fecha(fecha)
    bid = f"{sid}-B1"
    acciones = {
        "sacrificio": (sv.registrar_sacrificio, (sid, f), "Sacrificio registrado"),
        "edta": (sv.registrar_cambio_edta, (sid, f), "Cambio de EDTA registrado"),
        "enviar": (sv.enviar_a_histologia, (sid, f, forma), "Recepción en histología registrada"),
        "inclusion": (sv.registrar_inclusion, (bid, f), "Inclusión registrada"),
        "desgaste": (sv.cortar_par_desgaste, (bid, f, caja), "Par de desgaste registrado"),
        "revision": (sv.registrar_revision_sa, (bid, f, decision, protocolo), "Revisión SA registrada"),
        "set": (sv.cortar_set, (bid, f, protocolo, caja), "Set de corte registrado"),
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
    url = str(request.url_for("ver_placa", pid=pid))
    return pagina(request, "placa.html", "ratones", p=p, qr=qr_svg(url), url=url,
                  historial=sv.historial_placa(pid).to_dict("records"),
                  hermanas=sv.placas(p["sujeto_id"]).to_dict("records"),
                  resultados=sv.RESULTADOS, cajas=sv.cajas_placas())


@app.post("/placas/{pid}/tecnica")
@protegido
async def tecnica(request: Request, pid: int, tipo: str = Form(...), detalle: str = Form(""),
                  resultado: str = Form(...), comentario: str = Form(""), ubicacion: str = Form(""),
                  fecha: str = Form("")):
    tec = f"IHQ/IF {detalle}".strip() if tipo == "IHQ/IF" else f"Otra: {detalle}".strip()
    ejecutar(request, sv.registrar_tecnica, pid, a_fecha(fecha), tec, resultado, comentario,
             ubicacion or f"Con {usuario(request)['nombre']}", ok="Técnica registrada")
    return volver(f"/placas/{pid}")


@app.post("/placas/{pid}/mover")
@protegido
async def mover(request: Request, pid: int, destino: str = Form(""), otro: str = Form("")):
    ejecutar(request, sv.mover_placa, pid, otro.strip() or destino, date.today(), ok="Ubicación actualizada")
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
                  edta=[dict(f, dias=int(dias[f["id"]])) for f in df.to_dict("records") if f["id"] in dias])


@app.get("/histologia", response_class=HTMLResponse)
@protegido
async def histologia(request: Request):
    df = sv.ratones()
    grupos = [(p, df[df["paso_actual"] == p].to_dict("records")) for p in sv.PASOS_HISTO]
    return pagina(request, "histologia.html", "histologia", grupos=grupos)


@app.get("/tecnicas", response_class=HTMLResponse)
@protegido
async def tecnicas(request: Request):
    return pagina(request, "tecnicas.html", "tecnicas",
                  disponibles=sv.placas_para_tecnicas().to_dict("records"),
                  resultados=sv.resultados_recientes().to_dict("records"))


@app.get("/ubicaciones", response_class=HTMLResponse)
@protegido
async def ubicaciones(request: Request, ruta: str = ""):
    bloques, placas_ = sv.en_ubicacion(ruta) if ruta else (None, None)
    return pagina(request, "ubicaciones.html", "ubicaciones", arbol=sv.arbol_ubicaciones(), sel=ruta,
                  bloques=[] if bloques is None else bloques.to_dict("records"),
                  placas=[] if placas_ is None else placas_.to_dict("records"))


@app.post("/edta/{sid}")
@protegido
async def edta_rapido(request: Request, sid: str):
    ejecutar(request, sv.registrar_cambio_edta, sid, date.today(), ok=f"Cambio de EDTA registrado ({sid})")
    return volver(request.headers.get("referer") or "/")
