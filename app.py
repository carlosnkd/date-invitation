"""
app.py
------
Backend Flask para la aplicación romántica "¿Quieres salir conmigo?".

Responsabilidades:
    1. Servir la plantilla principal (index.html) con todo el flujo de pantallas.
    2. Recibir la respuesta final del usuario en la ruta POST /submit.
    3. Enviar un correo electrónico con el resumen del plan usando SMTP.

Las credenciales de correo NUNCA se escriben aquí directamente.
Se cargan desde un archivo .env mediante python-dotenv (ver README.md).
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuración inicial
# ---------------------------------------------------------------------------

# Carga las variables definidas en el archivo .env al entorno del proceso.
load_dotenv()

app = Flask(__name__)

# Variables de entorno para el envío de correo (definidas en .env)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")            # correo que envía
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip().replace(" ", "")  # contraseña de aplicación
DESTINATION_EMAIL = os.getenv("DESTINATION_EMAIL")  # correo que recibe la invitación aceptada


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Renderiza la página principal con todo el flujo (SPA de un solo archivo)."""
    return render_template("index.html")


@app.route("/test-email", methods=["GET"])
def test_email():
    """Endpoint de diagnóstico para probar el envío de correo."""
    email_sent = enviar_correo("Prueba", "Prueba", "Prueba")
    return jsonify({
        "status": "ok",
        "email_sent": email_sent,
        "message": "Correo de prueba enviado" if email_sent else "Correo de prueba fallido"
    }), 200


@app.route("/submit", methods=["POST"])
def submit():
    """
    Recibe la selección final del usuario (lugar, experiencia y fecha)
    y envía un correo electrónico con el resumen del plan.

    Body JSON esperado:
        {
            "lugar": "Cerro del Espolón",
            "experiencia": "Acampar",
            "fecha": "2026-08-20"
        }
    """
    print("[DEBUG] /submit endpoint called")
    print(f"[DEBUG] SMTP_EMAIL: {SMTP_EMAIL}")
    print(f"[DEBUG] DESTINATION_EMAIL: {DESTINATION_EMAIL}")

    data = request.get_json(silent=True) or {}

    lugar = data.get("lugar", "No especificado")
    experiencia = data.get("experiencia", "No especificado")
    fecha = data.get("fecha", "No especificado")

    # Si no hay credenciales configuradas, evitamos que la app truene:
    # devolvemos éxito "simulado" para que el frontend pueda seguir el flujo
    # (útil en desarrollo local sin .env configurado).
    if not SMTP_EMAIL or not SMTP_PASSWORD or not DESTINATION_EMAIL:
        app.logger.warning(
            "Variables SMTP no configuradas. Revisa tu archivo .env. "
            "No se envió ningún correo real."
        )
        print("[DEBUG] Missing SMTP variables")
        return jsonify({
            "status": "ok",
            "email_sent": False,
            "message": "Plan guardado (correo no enviado: configura .env)."
        }), 200

    try:
        email_sent = enviar_correo(lugar, experiencia, fecha)
        return jsonify({
            "status": "ok",
            "email_sent": email_sent,
            "message": "¡Correo enviado con éxito!" if email_sent else "Plan guardado, pero el correo no pudo enviarse."
        }), 200
    except Exception as error:
        print(f"[DEBUG] Error: {error}")
        app.logger.error(f"Error enviando correo: {error}")
        return jsonify({
            "status": "ok",
            "email_sent": False,
            "message": "Plan guardado, pero el correo no pudo enviarse."
        }), 200


def enviar_correo(lugar, experiencia, fecha):
    """Construye y envía el correo con el resumen del plan vía SMTP."""

    asunto = "Nuevo plan aceptado "

    cuerpo = f"""Nuevo plan aceptado

Lugar:
{lugar}

Experiencia:
{experiencia}

Fecha:
{fecha}
"""

    mensaje = MIMEMultipart()
    mensaje["From"] = SMTP_EMAIL
    mensaje["To"] = DESTINATION_EMAIL
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))

    try:
        # Conexión segura con el servidor SMTP (TLS) con timeout para evitar bloques en producción.
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, DESTINATION_EMAIL, mensaje.as_string())
        return True
    except Exception as error:
        app.logger.error(f"Error enviando correo: {error}")
        print(f"[DEBUG] SMTP error: {error}")
        return False


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
