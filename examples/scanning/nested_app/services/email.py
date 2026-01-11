"""Email implementation in services subdirectory."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable

from ..protocols import Email


@injectable(for_=Email)
@dataclass
class EmailService:
    """SMTP implementation of Email protocol."""

    smtp_host: str = "localhost"
    smtp_port: int = 587

    def send(self, to: str, subject: str, body: str) -> str:
        """Send an email."""
        return f"Sent email to {to}: {subject}"
