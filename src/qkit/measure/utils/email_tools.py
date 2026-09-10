import logging
import time
import traceback
from contextlib import AbstractContextManager
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

@dataclass(frozen=True)
class ExecutionMonitor(AbstractContextManager):
    email_config: EmailConfiguration
    task_name: str
    subject_tag: str = "AEM"
    exec_start_subject: str = "Execution Started"
    exec_end_subject: str = "Execution Ended"
    exec_failed_subject: str = "Execution Failed"

    def _format_status_message(self, condition: str, details: str | None = None) -> str:
        message = f"Task: {self.task_name}\r\nStatus: {condition}\r\nTime: {time.strftime('%H:%M:%S')}\r\nMonitored by Wrapper.\r\n"
        if details:
            message += "\r\n" + details + "\r\n"
        return message

    def __enter__(self):
        subject = f"[{self.subject_tag}] {self.task_name}: {self.exec_start_subject}"
        self.email_config.send(subject, self._format_status_message(self.exec_start_subject))

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            subject = f"[{self.subject_tag}] {self.task_name}: {self.exec_end_subject}"
            self.email_config.send(subject, self._format_status_message(self.exec_end_subject))
        else:
            subject = f"[{self.subject_tag}] {self.task_name}: {self.exec_failed_subject}"
            details = f"Exception: {exc_type.__name__}: {exc_val}\r\n"
            details += "\r\n".join(traceback.format_tb(exc_tb))
            self.email_config.send(subject, details)

