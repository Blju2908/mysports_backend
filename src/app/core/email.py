from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from starlette.background import BackgroundTasks
from app.core.config import Settings

settings = Settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
)

async def send_verification_email(email: EmailStr, username: str, token: str, background_tasks: BackgroundTasks):
    verification_link = f"http://localhost:3000/verify-email?token={token}"
    subject = "Bitte bestätige deine E-Mail-Adresse"
    body = f"Hallo {username},<br><br>Bitte bestätige deine E-Mail-Adresse, indem du auf folgenden Link klickst:<br><a href='{verification_link}'>{verification_link}</a><br><br>Viele Grüße,<br>Dein Team"
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="html"
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

async def send_password_reset_email(email: EmailStr, username: str, token: str, background_tasks: BackgroundTasks):
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    subject = "Passwort zurücksetzen"
    body = f"Hallo {username},<br><br>Du kannst dein Passwort zurücksetzen, indem du auf folgenden Link klickst:<br><a href='{reset_link}'>{reset_link}</a><br><br>Falls du das nicht warst, ignoriere diese E-Mail.<br><br>Viele Grüße,<br>Dein Team"
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="html"
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message) 