"""Pantallas del prototipo (etapa 2: solo consulta).

Ejecutar:  streamlit run app.py
"""
import streamlit as st

import servicios as sv

st.set_page_config(page_title="Defectos óseos · trazabilidad", page_icon="🐭", layout="wide")

if "vista" not in st.session_state:
    st.session_state.vista, st.session_state.sid = "menu", None


def ir(vista, sid=None):
    st.session_state.vista, st.session_state.sid = vista, sid
    for k in ("placa_desgaste", "placa_set"):
        st.session_state.pop(k, None)


def volver(*destinos):
    cols = st.columns(len(destinos) + 4)
    for col, (etiqueta, vista) in zip(cols, destinos):
        col.button(etiqueta, on_click=ir, args=(vista,), key=f"volver_{vista}")


def boton_raton(fila, extra="", key=""):
    st.button(f"🐭 **{fila['id']}** · {fila['paso_actual']} · HE: {fila['he']} · 📍 {fila['donde']}{extra}",
              on_click=ir, args=("raton", fila["id"]), key=f"r_{key}_{fila['id']}", width="stretch")


def aviso_edta():
    al = sv.alertas_edta()
    if al.empty or not al["toca_cambio"].any():
        return
    toca = al[al["toca_cambio"]]
    with st.container(border=True):
        st.error(f"⚠️ **Cambiar EDTA** · {len(toca)} ratón(es) llevan "
                 f"{sv.DIAS_CAMBIO_EDTA} o más días sin cambio")
        for _, a in toca.iterrows():
            st.button(f"🧪 {a['id']} · último cambio hace {a['dias']} días",
                      on_click=ir, args=("raton", a["id"]), key=f"edta_{a['id']}")


# ======================= MENÚ =======================
def menu():
    st.title("🐭 Defectos óseos · trazabilidad")
    st.caption("Prototipo con datos ficticios · solo consulta")
    aviso_edta()
    c = sv.conteo_por_paso()
    tarjetas = [
        ("🐭", "Ratones", "Ficha de cada ratón: paso actual, placas, imagenología e historial",
         f"{sum(c.values())} ratones", "ratones"),
        ("🧫", "Manejo", "Ratones en experimentación, sacrificio y decalcificación (EDTA)",
         f"{c['En experimentación']} vivos · {c['Decalcificación']} en EDTA", "manejo"),
        ("🔬", "Histología", "Todo lo que se está haciendo en histología, por paso",
         f"{sum(c[p] for p in sv.PASOS_HISTO if p not in ('Placas en técnicas', 'Archivado'))} en curso",
         "histologia"),
        ("🧪", "Técnicas", "Placas disponibles para IHQ/IF y resultados registrados",
         f"{c['Placas en técnicas']} ratones con placas", "tecnicas"),
    ]
    for fila in (tarjetas[:2], tarjetas[2:]):
        cols = st.columns(2)
        for col, (icono, titulo, desc, dato, vista) in zip(cols, fila):
            with col.container(border=True):
                st.markdown(f"<div style='font-size:3rem'>{icono}</div>", unsafe_allow_html=True)
                st.subheader(titulo)
                st.caption(desc)
                st.markdown(f"**{dato}**")
                st.button("Abrir", on_click=ir, args=(vista,), key=f"m_{vista}", width="stretch")


# ======================= RATONES =======================
def lista_ratones():
    volver(("⌂ Menú", "menu"))
    st.title("🐭 Ratones")
    a, b = st.columns([2, 1])
    busq = a.text_input("Buscar por número")
    paso = b.selectbox("Paso", ["Todos"] + sv.PASOS)
    df = sv.ratones(busq, paso)
    if df.empty:
        st.info("No hay ratones que coincidan.")
    for _, f in df.iterrows():
        boton_raton(f, key="lista")


ICONO = {"perdida": "❌", "en proceso": "🟡", "repetir": "🟠"}


def icono_placa(p):
    if p["tecnica"] == "HE":
        return "🟣"
    if p["tecnica"]:
        return ICONO.get(p["resultado"], "🟢")
    return "➕" if p["tipo_portaobjeto"] == "cargado" else "⚪"


def tira(df, clave, otra):
    if df.empty:
        return
    etiquetas = {int(p["id"]): f"{icono_placa(p)} {p['correlativo']}" for _, p in df.iterrows()}
    st.pills(clave.replace("placa_", "").capitalize(), list(etiquetas), format_func=etiquetas.get,
             key=clave, on_change=lambda: st.session_state.pop(otra, None))


def detalle_placa(p):
    with st.container(border=True):
        st.markdown(f"#### Placa {p['correlativo']} · serie {p['serie']}")
        a, b = st.columns(2)
        a.markdown(f"""
**Portaobjeto:** {p['tipo_portaobjeto']}  
**Destino al cortar:** {p['destino']} ({p['protocolo']})  
**Fecha de corte:** {p['fecha_corte']}  
**Técnica:** {p['tecnica'] or 'pendiente'}  
**Fecha técnica:** {p['fecha_tecnica'] or '—'}""")
        b.markdown(f"""
**Estado:** {p['estado']}  
**📍 Ubicación:** {p['ubicacion']}  
**Resultado:** {p['resultado'] or '—'}{f" ({p['quien']})" if p['quien'] else ''}  
**Comentario:** {p['comentario'] or '—'}""")
        if p["rotulo"]:
            st.markdown("**Rótulo**")
            st.code("\n".join(p["rotulo"].split(" | ")), language=None)
        else:
            st.caption("Sin rótulo: se rotula al hacer la técnica.")
        if p["tecnica"] == "HE":
            st.info("🖼️ Imagen HE: sin cargar todavía.")
        h = sv.historial_placa(p["id"])
        if not h.empty:
            st.markdown("**Historial de la placa**")
            st.dataframe(h, hide_index=True, width="stretch")


def ficha_raton():
    volver(("⌂ Menú", "menu"), ("← Ratones", "ratones"))
    r = sv.raton(st.session_state.sid)
    d = r["datos"]
    st.title(f"🐭 Ratón {r['id']}")
    st.caption(f"{d['grupo']} · defecto izq.: {d['contenido_defecto_izq']} · "
               f"defecto der.: {d['contenido_defecto_der']}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Paso actual", r["paso_actual"])
    m2.metric("Último trabajo", (r["ultimo"] or "—").split(" · ")[0],
              (r["ultimo"] or " · ").split(" · ")[1], delta_color="off")
    m3.metric("📍 Dónde está", r["donde"])
    antes = (r["ultimo"] or "").split(" · ")[0]
    sigue = sv.SIGUIENTE.get(r["paso_actual"])
    st.caption(" → ".join(x for x in [f"✓ {antes}" if antes else "",
                                       f"▶ **{r['paso_actual']}**",
                                       f"{sigue}" if sigue else ""] if x))

    t_placas, t_manejo, t_img, t_datos, t_hist = st.tabs(
        ["🔬 Placas", "🧫 Manejo", "🩻 Imagenología", "📋 Datos", "🕓 Historial"])

    with t_placas:
        df = sv.placas(r["id"])
        if df.empty:
            st.info("Aún no hay placas para este ratón.")
        else:
            st.caption("🟣 HE teñida · ⚪ normal sin teñir · ➕ cargada disponible · "
                       "🟢 técnica realizada · 🟡 en proceso · 🟠 repetir · ❌ perdida")
            tira(df[df["serie"] == "desgaste"], "placa_desgaste", "placa_set")
            tira(df[df["serie"] == "set"], "placa_set", "placa_desgaste")
            sel = st.session_state.get("placa_desgaste") or st.session_state.get("placa_set")
            if sel:
                detalle_placa(df[df["id"] == sel].iloc[0])
            else:
                st.caption("Toca una placa para ver su detalle.")

    with t_manejo:
        a, b = st.columns(2)
        a.markdown(f"""
**Cirugía:** {d['fecha_cirugia']}  
**Defecto izquierdo:** {d['contenido_defecto_izq']}  
**Defecto derecho:** {d['contenido_defecto_der']}  
**Tiempo de experimentación:** {d['tiempo_experimentacion']}  
**Sacrificio / formalina:** {d['fecha_sacrificio'] or 'vivo'}""")
        dec, cambios = sv.decalcificacion(r["id"])
        if dec:
            b.markdown(f"""
**Decalcificación EDTA**  
Inicio: {dec['fecha_inicio']}  
Fin: {dec['fecha_fin'] or 'en curso'}  
Cambios de EDTA: {len(cambios)}""")
            al = sv.alertas_edta()
            fila = al[al["id"] == r["id"]] if not al.empty else al
            if not fila.empty:
                dias = int(fila.iloc[0]["dias"])
                (b.error if dias >= sv.DIAS_CAMBIO_EDTA else b.success)(
                    f"Último cambio hace {dias} días" + (" · ⚠️ toca cambiar EDTA" if dias >= sv.DIAS_CAMBIO_EDTA else ""))
            with st.expander("Ver cambios de EDTA"):
                st.dataframe(cambios, hide_index=True, width="stretch")
        pp = sv.procesamiento_previo(r["id"])
        if not pp.empty:
            st.markdown("**Procesamiento previo**")
            st.dataframe(pp, hide_index=True, width="stretch")

    with t_img:
        img = sv.imagenologia(r["id"])
        if img.empty:
            st.info("Sin estudios de imagen.")
        for _, e in img.iterrows():
            st.markdown(f"**{e['tipo']}** · {e['lugar']} · {e['fecha']}")
            if e["vista_previa"]:
                st.image(e["vista_previa"])
            else:
                st.info("Vista previa sin cargar todavía.")
            if e["archivo_original"]:
                st.link_button("Descargar reconstrucción original", e["archivo_original"])

    with t_datos:
        bl = r["bloque_info"]
        st.markdown(f"""
**Sexo:** {d['sexo']} · **Nacimiento:** {d['fecha_nacimiento']} · **Caja:** {d['caja']}  
**Experimento:** {d['experimento']} · **Tesis:** {d['tesis_responsable']}  
**Anestesia:** {d['anestesia']} · **Lista:** {d['lista'] or '—'}""")
        if bl:
            st.markdown(f"""**Bloque:** {bl['id']} · llegó como {bl['forma_llegada']} el {bl['fecha_recepcion']}  
**Reinclusión:** {bl['fecha_reinclusion'] or 'pendiente'} · **📍** {bl['ubicacion']}""")
        st.caption(d["comentarios"] or "")

    with t_hist:
        st.dataframe(sv.historial(r["id"]), hide_index=True, width="stretch")


# ======================= MANEJO =======================
def manejo():
    volver(("⌂ Menú", "menu"))
    st.title("🧫 Manejo")
    aviso_edta()
    df = sv.ratones()
    st.subheader("En experimentación (vivos)")
    for _, f in df[df["paso_actual"] == "En experimentación"].iterrows():
        boton_raton(f, key="vivo")
    st.subheader("En decalcificación (EDTA)")
    al = sv.alertas_edta().set_index("id")
    for _, f in df[df["id"].isin(al.index)].iterrows():
        dias = int(al.loc[f["id"], "dias"])
        boton_raton(f, extra=f" · último cambio EDTA hace {dias} d" + (" ⚠️" if dias >= sv.DIAS_CAMBIO_EDTA else ""),
                    key="edta")


# ======================= HISTOLOGÍA =======================
def histologia():
    volver(("⌂ Menú", "menu"))
    st.title("🔬 Histología")
    st.caption("Ratones agrupados por el paso en que están")
    df = sv.ratones()
    for paso in sv.PASOS_HISTO:
        grupo = df[df["paso_actual"] == paso]
        with st.expander(f"**{paso}** ({len(grupo)})",
                         expanded=bool(len(grupo)) and paso not in ("Placas en técnicas", "Archivado")):
            if grupo.empty:
                st.caption("Nada en este paso.")
            for _, f in grupo.iterrows():
                boton_raton(f, extra=f" · último: {f['ultimo']}", key=paso)


# ======================= TÉCNICAS =======================
def tecnicas():
    volver(("⌂ Menú", "menu"))
    st.title("🧪 Técnicas")
    st.subheader("Placas disponibles para técnicas")
    st.dataframe(sv.placas_para_tecnicas(), hide_index=True, width="stretch")
    st.subheader("Resultados registrados")
    st.dataframe(sv.resultados_recientes(), hide_index=True, width="stretch")


{"menu": menu, "ratones": lista_ratones, "raton": ficha_raton, "manejo": manejo,
 "histologia": histologia, "tecnicas": tecnicas}[st.session_state.vista]()
