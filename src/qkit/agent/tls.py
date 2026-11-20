"""
TLS (SSL) settings for the qkit MCP server.

The MCP server is served over HTTPS by default. If no certificate is
configured, a self-signed certificate is generated automatically on the
first start and reused afterwards. Note that clients have to accept the
self-signed certificate explicitly (e.g. `insecure=True` for the mcp
python client).

Available configuration keys (qkit.cfg / qkit_local_config.py):
    mcp_ssl:            Serve the MCP server over HTTPS (default). Set to False for plain HTTP.
    mcp_host / mcp_port: Bind address of the MCP server (default localhost:8000).
    mcp_ssl_certfile:   PEM certificate file. Defaults to the generated self-signed certificate.
    mcp_ssl_keyfile:    PEM private key file. Defaults to the key generated next to the certificate.
    mcp_ssl_ca_certs:   Optional CA bundle used by uvicorn to require/validate client certificates.
"""

import ipaddress
import logging
import os
from datetime import datetime, timedelta, timezone

import qkit

log = logging.getLogger(__name__)

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8000

_CERT_DIR = 'certs'
_CERT_FILE = 'mcp_cert.pem'
_KEY_FILE = 'mcp_key.pem'


class TLSConfig():

    def __init__(self):
        self.host = qkit.cfg.get('mcp_host', DEFAULT_HOST)
        self.port = int(qkit.cfg.get('mcp_port', DEFAULT_PORT))

    def get_bind_address(self) -> tuple[str, int]:
        return self.host, self.port

    def get_base_url(self) -> str:
        return f'https://{self.host}:{self.port}'

    def get_ssl_kwargs(self) -> dict:
        """uvicorn keyword arguments for TLS, or an empty dict for plain HTTP.

        If HTTPS is enabled but no certificate is configured, a self-signed
        certificate is generated (and reused on subsequent starts).
        """
        certfile = qkit.cfg.get('mcp_ssl_certfile')
        keyfile = qkit.cfg.get('mcp_ssl_keyfile')
        if not certfile or not keyfile:
            certfile, keyfile = self.generate_self_signed_certificate()
        kwargs = {'ssl_certfile': certfile, 'ssl_keyfile': keyfile}
        ca_certs = qkit.cfg.get('mcp_ssl_ca_certs')
        if ca_certs:
            kwargs['ssl_ca_certs'] = ca_certs
        return kwargs


    def generate_self_signed_certificate(self) -> tuple[str, str]:
        """Generate a self-signed certificate and private key, unless they already exist.

        Returns (certfile, keyfile). The files are stored under <qkitdir>/certs.
        The certificate is valid for localhost, 127.0.0.1, ::1 and the configured
        mcp_host (if it is a host name).
        """
        cert_dir = os.path.join(qkit.cfg['logdir'], _CERT_DIR)
        certfile = os.path.join(cert_dir, _CERT_FILE)
        keyfile = os.path.join(cert_dir, _KEY_FILE)
        if os.path.exists(certfile) and os.path.exists(keyfile):
            return certfile, keyfile

        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.x509.oid import NameOID
        except ImportError as exc:
            raise RuntimeError(
                "HTTPS is enabled for the MCP server, but no certificate is configured and the "
                "'cryptography' package is missing (needed to generate a self-signed certificate). "
                "Install cryptography or set mcp_ssl_certfile/mcp_ssl_keyfile in qkit.cfg."
            ) from exc

        os.makedirs(cert_dir, exist_ok=True)

        host, _ = self.get_bind_address()
        names = ['localhost', '127.0.0.1', '::1']
        if host not in names:
            names.append(host)
        subject_alt_names = []
        for name in names:
            try:
                subject_alt_names.append(x509.IPAddress(ipaddress.ip_address(name)))
            except ValueError:
                subject_alt_names.append(x509.DNSName(name))

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'qkit-mcp')])
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=3650))
            .add_extension(x509.SubjectAlternativeName(subject_alt_names), critical=False)
            .sign(key, hashes.SHA256())
        )

        with open(certfile, 'wb') as file:
            file.write(cert.public_bytes(serialization.Encoding.PEM))
        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        # Restrict key file permissions to the owner.
        descriptor = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, 'wb') as file:
            file.write(key_bytes)

        log.info("Generated self-signed certificate for the MCP server: %s", certfile)
        return certfile, keyfile
