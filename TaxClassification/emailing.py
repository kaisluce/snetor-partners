import asyncio
import configparser
import sys
from pathlib import Path

from msgraph.generated.models.file_attachment import FileAttachment
from azure.identity import CertificateCredential
from msgraph.graph_service_client import GraphServiceClient
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody,
)

# Microsoft Graph email helper: loads config/cert and sends reports.
# Charge clientId/tenantId depuis config.cfg (et config.dev.cfg si present)
BASE_DIR = Path(__file__).resolve().parent
#DEFAULT_RECIPIENT = "masterdata@snetor.com"
DEFAULT_RECIPIENT = "k.luce@snetor.com"
CHANGE_TEMPLATE = (
    "Vous trouverez en piece jointe le rapport listant les partenaires avec une Tax Classification mal renseignee."
)

NO_CHANGE_TEMPLATE = (
    "Toutes les donnees de Tax Classification sont conformes."
)
ERROR_TEMPLATE = (
    "<p>"
    "Une erreur est survenue lors du controle Tax Classification. Voici le message d'erreur :"
    "{error_message}"
    "</p>"
)


SUBJECT = "bp tax classification"

def _candidate_paths() -> list[Path]:
    """
    Build a list of possible config locations.

    We check:
    - alongside this module (source checkout or inside the PyInstaller bundle)
    - alongside the executable (PyInstaller onefile)
    - the parent project folder
    - the current working directory
    """
    exe_dir = Path(sys.argv[0]).resolve().parent
    runtime_dir = Path(getattr(sys, "_MEIPASS", BASE_DIR))
    candidates = [
        BASE_DIR / "config.cfg",
        BASE_DIR / "config.dev.cfg",
        BASE_DIR.parent / "config.cfg",
        BASE_DIR.parent / "config.dev.cfg",
        exe_dir / "config.cfg",
        exe_dir / "config.dev.cfg",
        runtime_dir / "config.cfg",
        runtime_dir / "config.dev.cfg",
        Path.cwd() / "config.cfg",
        Path.cwd() / "config.dev.cfg",
    ]
    # Preserve order but drop duplicates
    seen = set()
    unique = []
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def _log_helpers(logger=None):
    def _info(msg):
        if logger is None:
            print(f"[MAIL] {msg}")
        elif hasattr(logger, "log"):
            logger.log(msg)
        elif hasattr(logger, "info"):
            logger.info(msg)
        else:
            logger(msg)

    def _warn(msg):
        if logger is None:
            print(f"[MAIL][WARN] {msg}")
        elif hasattr(logger, "warn"):
            logger.warn(msg)
        elif hasattr(logger, "warning"):
            logger.warning(msg)
        else:
            _info(f"[WARN] {msg}")

    def _error(msg):
        if logger is None:
            print(f"[MAIL][ERROR] {msg}")
        elif hasattr(logger, "error"):
            logger.error(msg)
        else:
            _info(f"[ERROR] {msg}")
    return _info, _warn, _error


def _get_subject(has_attachment: bool) -> str:
    _ = has_attachment
    return f"MDM Quality Check Report - [ {SUBJECT} ]"


def _load_config(logger=None) -> configparser.ConfigParser:
    """
    Load azure settings lazily so the application can run even when the config
    is missing (e.g., when emails are disabled).
    """
    config = configparser.ConfigParser(interpolation=None)
    candidates = _candidate_paths()
    read_files = config.read(candidates)
    if "azure" not in config:
        tried = ", ".join(str(p) for p in candidates)
        read = ", ".join(read_files) if read_files else "none"
        raise RuntimeError(f"No [azure] section found. Tried: {tried}. Loaded: {read}.")
    return config

async def main(file_path : str | None = None, logger=None) -> None:
    info, warn, error = _log_helpers(logger)
    config = _load_config(logger=logger)
    azure_settings = config["azure"]
    tenant_id = azure_settings["tenantId"]
    client_id = azure_settings["clientId"]

    # PFX place a la racine du projet par defaut, surcharge possible via config
    cert_path_setting = azure_settings.get("certificatePath", "MDMPythonGraphV2.pfx")
    cert_path = Path(cert_path_setting)
    if not cert_path.is_absolute():
        # Resolve relative paths from the emailing/ directory so the script remains portable
        cert_path = (BASE_DIR / cert_path).resolve()
    cert_password = azure_settings.get("certificatePassword") or None
    if cert_password and cert_password.startswith('"') and cert_password.endswith('"'):
        cert_password = cert_password[1:-1]

    shared_mailbox_upn = "mdm.report@snetor.com"

    credential = CertificateCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        certificate_path=str(cert_path),
        password=cert_password,
    )

    graph = GraphServiceClient(credential, scopes=["https://graph.microsoft.com/.default"])
    info(f"Prepared Graph client for mailbox send. Attachment={file_path}")
    
    has_attachment = file_path is not None
    mail_body = CHANGE_TEMPLATE if has_attachment else NO_CHANGE_TEMPLATE
    subject_line = _get_subject(has_attachment)

    message = Message(
        subject=subject_line,
        body=ItemBody(
            content_type=BodyType.Html,
            content=mail_body,
        ),
        to_recipients=[
            Recipient(email_address=EmailAddress(address=DEFAULT_RECIPIENT))
            # Recipient(email_address=EmailAddress(address="k.luce@snetor.com"))
        ],
    )

    info(f"filepath: {file_path}")
    if has_attachment:
        file = Path(file_path)

        # Pass raw bytes; the SDK handles base64 encoding when serializing
        attachment = FileAttachment(
            name=file.name,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            content_bytes=file.read_bytes(),
        )
        
        message.attachments=[attachment]
        
    request_body = SendMailPostRequestBody(
        message=message,
        save_to_sent_items=True,
    )

    await graph.users.by_user_id(shared_mailbox_upn).send_mail.post(request_body)
    info("Mail envoye avec succes.")


def sendmail(file_path: str | None = None, logger=None) -> asyncio.Future:
    """
    Backwards-compatible wrapper used by callers expecting sendmail().
    """
    return main(file_path, logger=logger)


async def errormail(error_message: str, subject: str = SUBJECT, logger=None) -> None:
    """
    Send an error notification email with the provided message (no attachment).
    """
    _info, _warn, _error = _log_helpers(logger)
    config = _load_config(logger=logger)
    azure_settings = config["azure"]
    tenant_id = azure_settings["tenantId"]
    client_id = azure_settings["clientId"]

    # PFX place a la racine du projet par defaut, surcharge possible via config
    cert_path_setting = azure_settings.get("certificatePath", "MDMPythonGraphV2.pfx")
    cert_path = Path(cert_path_setting)
    if not cert_path.is_absolute():
        # Resolve relative paths from the emailing/ directory so the script remains portable
        cert_path = (BASE_DIR / cert_path).resolve()
    cert_password = azure_settings.get("certificatePassword") or None
    if cert_password and cert_password.startswith('"') and cert_password.endswith('"'):
        cert_password = cert_password[1:-1]

    shared_mailbox_upn = "mdm.report@snetor.com"

    credential = CertificateCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        certificate_path=str(cert_path),
        password=cert_password,
    )

    graph = GraphServiceClient(credential, scopes=["https://graph.microsoft.com/.default"])
    _info("Preparing error email")

    message = Message(
        subject=f"[MDM Enrichissement BP] {subject}",
        body=ItemBody(
            content_type=BodyType.Html,
            content=ERROR_TEMPLATE.format(error_message=error_message),
        ),
        to_recipients=[
            Recipient(email_address=EmailAddress(address=DEFAULT_RECIPIENT))
        ],
    )

    request_body = SendMailPostRequestBody(
        message=message,
        save_to_sent_items=True,
    )

    await graph.users.by_user_id(shared_mailbox_upn).send_mail.post(request_body)
    _info("Error email sent successfully.")


if __name__ == "__main__":
    asyncio.run(main("missing_siren_found", r"\\snetor-docs\Users\MDM\998_CHecks\ENRISHED-BP\missing_siren_found.xlsx"))










