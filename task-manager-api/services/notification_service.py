import logging
import smtplib
from email.message import EmailMessage

from config.settings import settings

log = logging.getLogger(__name__)


class NotificationService:
    """Envia notificações por email. Credenciais via env (NUNCA hardcoded)."""

    def __init__(self, host: str, port: int, user: str, password: str, enabled: bool):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.enabled = enabled and bool(host and user and password)

    @classmethod
    def from_settings(cls) -> 'NotificationService':
        return cls(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            user=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            enabled=settings.NOTIFICATIONS_ENABLED,
        )

    def send_email(self, to: str, subject: str, body: str) -> bool:
        if not self.enabled:
            log.info('notification.disabled', extra={'to': to, 'subject': subject})
            return False
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = to
            msg.set_content(body)
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            log.info('notification.sent', extra={'to': to})
            return True
        except Exception:
            log.exception('notification.failed')
            return False
