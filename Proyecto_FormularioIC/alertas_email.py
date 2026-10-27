"""Generación y envío de alertas por canal con control de entregas."""
import os
import smtplib
import ssl
from email.message import EmailMessage

from calculos import calcular_resultado
from html import escape
from models import (
    Alerta,
    Analista,
    CoordinadorCanal,
    EncuestaAlicorp,
    EncuestaInterna,
    Reporte,
    EntregaAlertaCoordinador,
    db,
)


def enviar_correo(destino, asunto, cuerpo):
    if os.getenv("MAIL_BACKEND", "smtp").strip().lower() == "outlook":
        try:
            import win32com.client

            outlook = win32com.client.Dispatch("Outlook.Application")
            mensaje = outlook.CreateItem(0)
            mensaje.To = destino
            mensaje.Subject = asunto
            mensaje.HTMLBody = cuerpo
            cuenta = os.getenv("SMTP_FROM", "").strip().lower()
            if cuenta:
                cuentas = outlook.Session.Accounts
                coincidencias = [
                    cuentas.Item(i)
                    for i in range(1, cuentas.Count + 1)
                    if str(cuentas.Item(i).SmtpAddress).lower() == cuenta
                ]
                if not coincidencias:
                    raise RuntimeError(
                        f"La cuenta {cuenta} no está configurada en Outlook de escritorio."
                    )
                mensaje.SendUsingAccount = coincidencias[0]
            mensaje.Send()
            return
        except ImportError as exc:
            raise RuntimeError(
                "Instala pywin32 en el entorno Python del proyecto para usar Outlook."
            ) from exc

    servidor = os.getenv("SMTP_HOST", "").strip()
    remitente = os.getenv("SMTP_FROM", "").strip()
    if not servidor or not remitente:
        raise RuntimeError("Configura SMTP_HOST y SMTP_FROM antes de enviar alertas.")

    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content("Tu cliente de correo no puede mostrar este mensaje en formato HTML.")
    mensaje.add_alternative(cuerpo, subtype="html")
    puerto = int(os.getenv("SMTP_PORT", "587"))
    usuario = os.getenv("SMTP_USER", "")
    clave = os.getenv("SMTP_PASSWORD", "")

    if os.getenv("SMTP_SSL", "false").lower() == "true":
        conexion = smtplib.SMTP_SSL(
            servidor, puerto, timeout=20, context=ssl.create_default_context()
        )
    else:
        conexion = smtplib.SMTP(servidor, puerto, timeout=20)

    with conexion:
        if os.getenv("SMTP_SSL", "false").lower() != "true":
            conexion.starttls(context=ssl.create_default_context())
        if usuario:
            conexion.login(usuario, clave)
        conexion.send_message(mensaje)


def _agregar_lectura(nombre, puntaje, fortalezas, oportunidades):
    if puntaje is None:
        return
    if puntaje >= 8:
        fortalezas.append(f"{nombre}: {puntaje}/10.")
    elif puntaje <= 6:
        oportunidades.append(f"{nombre}: {puntaje}/10.")


def detalle_analista(analista, periodo, motivos):
    interna = EncuestaInterna.query.filter_by(
        analista_id=analista.id,
        periodo=periodo
    ).first()

    alicorp = EncuestaAlicorp.query.filter_by(
        analista_id=analista.id,
        periodo=periodo
    ).first()

    resultado = calcular_resultado(
        analista, periodo, Reporte, EncuestaInterna, EncuestaAlicorp
    )

    fortalezas = []
    oportunidades = []

    componentes_internos = [
        ("Cumplimiento", resultado["cumplimiento_interno"]),
        ("Calidad", resultado["calidad_interna"]),
        ("Autonomía", resultado["autonomia"]),
        ("Prevención y comunicación", resultado["prevencion_comunicacion"]),
        ("Mejora continua", resultado["mejora_continua"]),
    ]

    componentes_alicorp = [
        ("Solicita datos a tiempo", resultado.get("solicita_datos_tiempo")),
        ("Envía a validar en plazo", resultado.get("envia_validar_plazo")),
        ("Publica/envía reportes a tiempo", resultado.get("publica_reportes_tiempo")),
        ("Participa en reuniones clave", resultado.get("participa_reuniones")),
        ("Comunica incidencias a tiempo", resultado.get("comunica_incidencias_tiempo")),
        ("Resuelve incidencias a tiempo", resultado.get("resuelve_incidencias_tiempo")),
        ("Capacita ante actualizaciones", resultado.get("capacita_actualizaciones")),
        ("Comunica status de avances", resultado.get("comunica_status_tiempo")),
    ]

    for nombre, puntaje in componentes_internos + componentes_alicorp:
        if puntaje is not None:
            _agregar_lectura(nombre, puntaje, fortalezas, oportunidades)

    filas_interno = ""
    for nombre, puntaje in componentes_internos:
        if puntaje is not None:
            filas_interno += f"""
            <tr>
                <td style="padding:10px 12px;border-bottom:1px solid #E5E7EB;font-size:13px;color:#334155;">
                    {escape(nombre)}
                </td>
                <td align="right" style="padding:10px 12px;border-bottom:1px solid #E5E7EB;font-size:13px;color:#0F172A;font-weight:bold;">
                    {puntaje}/10
                </td>
            </tr>
            """

    filas_alicorp = ""
    for nombre, puntaje in componentes_alicorp:
        if puntaje is not None:
            filas_alicorp += f"""
            <tr>
                <td style="padding:10px 12px;border-bottom:1px solid #E5E7EB;font-size:13px;color:#334155;">
                    {escape(nombre)}
                </td>
                <td align="right" style="padding:10px 12px;border-bottom:1px solid #E5E7EB;font-size:13px;color:#0F172A;font-weight:bold;">
                    {puntaje}/10
                </td>
            </tr>
            """

    motivos_html = "".join(
        f"<li style='margin-bottom:5px;'>{escape(m)}</li>"
        for m in motivos
    )

    fortalezas_html = "".join(
        f"<li style='margin-bottom:5px;'>{escape(f)}</li>"
        for f in fortalezas
    ) or "<li>No se identificaron fortalezas destacadas.</li>"

    oportunidades_html = "".join(
        f"<li style='margin-bottom:5px;'>{escape(o)}</li>"
        for o in oportunidades
    ) or "<li>No se identificaron oportunidades críticas.</li>"

    comentario = (
        alicorp.comentario.strip()
        if alicorp and alicorp.comentario and alicorp.comentario.strip()
        else "Sin comentario registrado."
    )

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
           style="border-collapse:collapse;margin-top:22px;border:1px solid #D9E2EC;">
        <tr>
            <td bgcolor="#F4F7FA" style="padding:18px 20px;">
                <table width="100%" cellspacing="0" cellpadding="0">
                    <tr>
                        <td>
                            <div style="font-family:Arial,sans-serif;font-size:17px;font-weight:bold;color:#0B2E4F;">
                                {escape(analista.nombre)}
                            </div>
                            <div style="font-family:Arial,sans-serif;font-size:12px;color:#64748B;margin-top:4px;">
                                Resultado del periodo {escape(periodo)}
                            </div>
                        </td>

                        <td align="right">
                            <div style="font-family:Arial,sans-serif;font-size:11px;color:#64748B;">
                                PUNTAJE FINAL
                            </div>
                            <div style="font-family:Arial,sans-serif;font-size:24px;font-weight:bold;color:#C62828;">
                                {resultado['nota_final']}/100
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>

        <tr>
            <td bgcolor="#FFFFFF" style="padding:18px 20px;">

                <div style="font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:#0F172A;margin-bottom:6px;">
                    Motivo de seguimiento
                </div>

                <ul style="font-family:Arial,sans-serif;font-size:13px;color:#475569;margin-top:6px;padding-left:20px;">
                    {motivos_html}
                </ul>


                <div style="font-family:Arial,sans-serif;font-size:14px;font-weight:bold;color:#0B2E4F;margin-top:22px;margin-bottom:8px;">
                    Evaluación interna - Controller
                </div>

                <table width="100%" cellspacing="0" cellpadding="0"
                       style="border-collapse:collapse;border:1px solid #E5E7EB;">
                    {filas_interno}
                    <tr>
                        <td bgcolor="#F8FAFC" style="padding:11px 12px;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:#0F172A;">
                            Nota interna
                        </td>
                        <td bgcolor="#F8FAFC" align="right" style="padding:11px 12px;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:#0F172A;">
                            {resultado['nota_interna']}/45
                        </td>
                    </tr>
                </table>


                <div style="font-family:Arial,sans-serif;font-size:14px;font-weight:bold;color:#0B2E4F;margin-top:22px;margin-bottom:8px;">
                    Evaluación Alicorp
                </div>

                <table width="100%" cellspacing="0" cellpadding="0"
                       style="border-collapse:collapse;border:1px solid #E5E7EB;">
                    {filas_alicorp}
                    <tr>
                        <td bgcolor="#F8FAFC" style="padding:11px 12px;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:#0F172A;">
                            Nota Alicorp
                        </td>
                        <td bgcolor="#F8FAFC" align="right" style="padding:11px 12px;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;color:#0F172A;">
                            {resultado['nota_alicorp']}/55
                        </td>
                    </tr>
                </table>


                <table width="100%" cellspacing="0" cellpadding="0"
                       style="margin-top:18px;border-collapse:collapse;">
                    <tr>
                        <td bgcolor="#F8FAFC" style="padding:14px;border-left:4px solid #0B2E4F;">
                            <div style="font-family:Arial,sans-serif;font-size:12px;font-weight:bold;color:#0B2E4F;margin-bottom:5px;">
                                COMENTARIO ALICORP
                            </div>
                            <div style="font-family:Arial,sans-serif;font-size:13px;color:#475569;">
                                {escape(comentario)}
                            </div>
                        </td>
                    </tr>
                </table>


                <table width="100%" cellspacing="0" cellpadding="0"
                       style="margin-top:20px;border-collapse:collapse;">
                    <tr>
                        <td width="50%" valign="top" style="padding-right:8px;">
                            <table width="100%" cellspacing="0" cellpadding="0"
                                   style="border-collapse:collapse;">
                                <tr>
                                    <td bgcolor="#F0FDF4" style="padding:12px;">
                                        <div style="font-family:Arial,sans-serif;font-size:12px;font-weight:bold;color:#166534;">
                                            FORTALEZAS
                                        </div>
                                        <ul style="font-family:Arial,sans-serif;font-size:12px;color:#334155;padding-left:18px;margin-bottom:0;">
                                            {fortalezas_html}
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </td>

                        <td width="50%" valign="top" style="padding-left:8px;">
                            <table width="100%" cellspacing="0" cellpadding="0"
                                   style="border-collapse:collapse;">
                                <tr>
                                    <td bgcolor="#FFF7ED" style="padding:12px;">
                                        <div style="font-family:Arial,sans-serif;font-size:12px;font-weight:bold;color:#9A3412;">
                                            OPORTUNIDADES DE MEJORA
                                        </div>
                                        <ul style="font-family:Arial,sans-serif;font-size:12px;color:#334155;padding-left:18px;margin-bottom:0;">
                                            {oportunidades_html}
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>

            </td>
        </tr>
    </table>
    """


def procesar_alertas(periodo):
    """Genera alertas y las envía al Coordinador activo del mismo canal."""
    if (
        os.getenv("MAIL_BACKEND", "smtp").strip().lower() != "outlook"
        and (not os.getenv("SMTP_HOST") or not os.getenv("SMTP_FROM"))
    ):
        raise ValueError("Falta configurar SMTP_HOST o SMTP_FROM.")

    for analista in Analista.query.filter_by(activo=True).all():
        resultado = calcular_resultado(
            analista, periodo, Reporte, EncuestaInterna, EncuestaAlicorp
        )
        if not resultado["evaluacion_completa"]:
            continue
        if resultado["nota_final"] < 75:
            motivo = f"Puntaje final: {resultado['nota_final']}/100 (< 75)"
            alerta = Alerta.query.filter_by(
                analista_id=analista.id, periodo=periodo, tipo="nota_baja"
            ).first()
            if alerta is None:
                db.session.add(
                    Alerta(
                        analista_id=analista.id,
                        periodo=periodo,
                        tipo="nota_baja",
                        motivo=motivo,
                    )
                )
            else:
                alerta.motivo = motivo
    db.session.commit()

    alertas = (
        db.session.query(Alerta, Analista)
        .join(Analista, Alerta.analista_id == Analista.id)
        .filter(
            Alerta.periodo == periodo,
            Alerta.tipo == "nota_baja",
            Analista.activo == True,
        )
        .all()
    )

    enviados, pendientes = 0, 0
    errores = []
    coordinadores = CoordinadorCanal.query.filter_by(activo=True).all()

    for coordinador in coordinadores:
        candidatos = [
            (alerta, analista)
            for alerta, analista in alertas
            if analista.canal.strip().casefold() == coordinador.canal.strip().casefold()
            and not EntregaAlertaCoordinador.query.filter_by(
                alerta_id=alerta.id, coordinador_id=coordinador.id
            ).first()
        ]
        if not candidatos:
            continue

        por_analista = {}
        for alerta, analista in candidatos:
            if analista.id not in por_analista:
                por_analista[analista.id] = {"analista": analista, "motivos": []}
            por_analista[analista.id]["motivos"].append(alerta.motivo)

        detalles = [
            detalle_analista(item["analista"], periodo, item["motivos"])
            for item in por_analista.values()
        ]
        cuerpo = f"""
        <html>
        <head>
            <meta name="color-scheme" content="light">
            <meta name="supported-color-schemes" content="light">
        </head>

        <body bgcolor="#F2F5F8"
            style="margin:0;padding:0;background-color:#F2F5F8;">

        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
            bgcolor="#F2F5F8"
            style="width:100%;border-collapse:collapse;">
            <tr>
                <td align="center" style="padding:30px 15px;">

                    <table role="presentation"
                        width="680"
                        cellspacing="0"
                        cellpadding="0"
                        bgcolor="#FFFFFF"
                        style="width:680px;border-collapse:collapse;background:#FFFFFF;border:1px solid #D9E2EC;">

                        <!-- CABECERA -->
                        <tr>
                            <td bgcolor="#0B2E4F"
                                style="padding:24px 28px;background:#0B2E4F;">

                                <div style="font-family:Arial,sans-serif;font-size:11px;font-weight:bold;letter-spacing:1px;color:#BFD4E7;">
                                    EVALUACIÓN IC
                                </div>

                                <div style="font-family:Arial,sans-serif;font-size:22px;font-weight:bold;color:#FFFFFF;margin-top:5px;">
                                    Alerta de seguimiento
                                </div>

                                <div style="font-family:Arial,sans-serif;font-size:13px;color:#DCE8F2;margin-top:6px;">
                                    Periodo {escape(periodo)}
                                </div>

                            </td>
                        </tr>

                        <!-- INTRODUCCIÓN -->
                        <tr>
                            <td bgcolor="#FFFFFF"
                                style="padding:26px 28px;background:#FFFFFF;">

                                <p style="font-family:Arial,sans-serif;font-size:14px;line-height:21px;color:#334155;margin:0 0 14px;">
                                    Hola <strong>{escape(coordinador.nombre)}</strong>,
                                </p>

                                <p style="font-family:Arial,sans-serif;font-size:14px;line-height:21px;color:#475569;margin:0;">
                                    Se identificó
                                    <strong>{len(por_analista)} analista(s)</strong>
                                    del canal
                                    <strong>{escape(coordinador.canal)}</strong>
                                    que requieren seguimiento debido a un puntaje final menor a
                                    <strong>75/100</strong>.
                                </p>

                                {''.join(detalles)}

                                <table width="100%" cellspacing="0" cellpadding="0"
                                    style="margin-top:24px;border-collapse:collapse;">
                                    <tr>
                                        <td bgcolor="#EFF6FF"
                                            style="padding:15px;border-left:4px solid #2563EB;">
                                            <div style="font-family:Arial,sans-serif;font-size:13px;line-height:19px;color:#1E3A8A;">
                                                Revisa el <strong>Dashboard de Evaluación IC</strong>
                                                para analizar el resultado y definir las acciones de seguimiento correspondientes.
                                            </div>
                                        </td>
                                    </tr>
                                </table>

                            </td>
                        </tr>

                        <!-- PIE -->
                        <tr>
                            <td bgcolor="#F8FAFC"
                                style="padding:16px 28px;border-top:1px solid #E5E7EB;">

                                <div style="font-family:Arial,sans-serif;font-size:11px;color:#64748B;">
                                    Mensaje generado automáticamente por el sistema de Evaluación IC.
                                </div>

                            </td>
                        </tr>

                    </table>

                </td>
            </tr>
        </table>

        </body>
        </html>
        """

        try:
            enviar_correo(
                coordinador.correo,
                f"Evaluación IC | Alerta {coordinador.canal} | {periodo}",
                cuerpo,
            )
            for alerta, _ in candidatos:
                db.session.add(
                    EntregaAlertaCoordinador(
                        alerta_id=alerta.id, coordinador_id=coordinador.id
                    )
                )
            db.session.commit()
            enviados += 1
        except (OSError, smtplib.SMTPException, RuntimeError) as exc:
            db.session.rollback()
            pendientes += 1
            errores.append(f"{coordinador.correo}: {exc}")

    # Si existe una alerta para un canal sin Coordinador activo, se reporta como pendiente.
    canales_con_coordinador = {c.canal.strip().casefold() for c in coordinadores}
    canales_sin_destino = sorted({
        analista.canal
        for alerta, analista in alertas
        if analista.canal.strip().casefold() not in canales_con_coordinador
    })
    for canal in canales_sin_destino:
        pendientes += 1
        errores.append(f"No existe un Coordinador activo para el canal {canal}.")

    return enviados, pendientes, errores

