"""Email service in services subdirectory."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable


@injectable
@dataclass
class EmailService:
    """Email service found in services/email.py."""

    smtp_host: str = "localhost"
    smtp_port: int = 587

    def send(self, to: str, subject: str, body: str) -> str:
        """Simulate sending email."""
        return f"Sent email to {to}: {subject}"
