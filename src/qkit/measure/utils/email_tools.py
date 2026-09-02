import logging
from dataclasses import dataclass
from typing import List

log = logging.getLogger(__name__)
try:
    import smtplib
except ImportError:
    log.error("smtplib required for email notifications!")

@dataclass
class EmailUser:
    address: str
    name: str

@dataclass
class EmailServerConfig:
    host: str
    port: int
    username: str | None = None
    password: str | None = None

    def send_email(self, sender_adr: str, recipient_addresses: List[str], content: str):
        with smtplib.SMTP_SSL(self.host, self.port) as server:
            if self.username and self.password:
                server.login(self.username, self.password)
            server.sendmail(sender_adr, recipient_addresses, content)

@dataclass(frozen=True)
class EmailConfiguration:
    server: EmailServerConfig
    sender: EmailUser
    recipients: List[EmailUser]

    def send(self, subject, content):
        headers = dict()
        headers["From"] = f"{self.sender.name} <{self.sender.address}>"
        headers["Reply-To"] = self.sender.address
        headers["To"] = ', '.join([f"{recp.name} <{recp.address}>" for recp in self.recipients])
        headers["Subject"] = subject
        headers["Auto-Submitted"] = "auto-generated"
        headers["Content-Type"] = "text/plain"

        header_payload = ""
        for k, v in headers.items():
            header_payload += f"{k}: {v}\r\n"

        payload = header_payload + "\r\n" + content
        self.server.send_email(self.sender.address, [recp.address for recp in self.recipients], payload)