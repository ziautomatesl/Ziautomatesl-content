import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from agents.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SENDER_EMAIL, SENDER_NAME


def send_email(to_email: str, subject: str, body: str, html: str = "") -> bool:
    if not to_email or "@" not in to_email:
        print(f"    Email inválido: {to_email!r}")
        return False

    if not SMTP_PASS:
        print(f"    [SIMULADO] → {to_email} | {subject[:50]}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"]      = to_email

    msg.attach(MIMEText(body, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        print(f"    Enviado a {to_email}")
        return True
    except Exception as e:
        print(f"    Error SMTP enviando a {to_email}: {e}")
        return False
