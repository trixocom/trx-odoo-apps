# Part of Trixocom.
"""Driver del proveedor whatsmeow vía sidecar **WuzAPI** (github.com/asternic/wuzapi, MIT).

WuzAPI es un servicio Go que embebe la librería whatsmeow y expone una API REST.
Lo corremos como contenedor aislado al lado de Odoo (sin puerto publicado), y Odoo
le habla por la red interna (p.ej. http://whatsmeow:8080).

Autenticación: header ``Token: <token-de-usuario>`` (uno por cuenta WhatsApp).
Respuestas WuzAPI: ``{"code":200,"data":{...},"success":true}``.

Cada cuenta de Odoo (whatsapp.account) = un "usuario" de WuzAPI con su token y su
webhook propio. La recepción llega por webhook a /trixo_whatsapp/whatsmeow/webhook
(firmado con HMAC ``x-hmac-signature``).

Riesgo: conexión directa = viola ToS de WhatsApp, puede derivar en baneo. Asumido.
"""
import base64
import logging

import requests

from .base import WhatsAppTransport, WhatsAppTransportError, register_transport

_logger = logging.getLogger(__name__)

TIMEOUT = (10, 60)


@register_transport
class WhatsmeowTransport(WhatsAppTransport):
    provider = "whatsmeow"
    capabilities = frozenset({"media", "reactions", "qr"})

    @property
    def _base(self):
        base = (self.account.whatsmeow_base_url or "").rstrip("/")
        if not base:
            raise WhatsAppTransportError("Sidecar WuzAPI sin URL configurada.",
                                         failure_type="account")
        return base

    def _headers(self):
        token = self.account.sudo().whatsmeow_token
        if not token:
            raise WhatsAppTransportError("Cuenta sin token de WuzAPI.",
                                         failure_type="account")
        return {"Token": token, "Content-Type": "application/json"}

    def _request(self, method, path, *, json=None):
        try:
            res = requests.request(method, self._base + path, json=json,
                                   headers=self._headers(), timeout=TIMEOUT)
        except requests.exceptions.RequestException as err:
            raise WhatsAppTransportError(str(err), failure_type="network") from err
        if not res.ok:
            raise WhatsAppTransportError("WuzAPI HTTP %s: %s" %
                                         (res.status_code, res.text[:200]))
        body = res.json()
        if isinstance(body, dict) and body.get("success") is False:
            raise WhatsAppTransportError(str(body.get("error") or body))
        return body.get("data", {}) if isinstance(body, dict) else {}

    # ------------------------------------------------------------------ #
    #  Sesión / QR
    # ------------------------------------------------------------------ #
    def status(self):
        try:
            data = self._request("GET", "/session/status")
        except WhatsAppTransportError:
            return "error"
        if data.get("LoggedIn"):
            return "connected"
        if data.get("Connected"):
            return "qr_pending"
        return "logged_out"

    def connect(self):
        # Subscribe a Message + ReadReceipt; Immediate=true devuelve enseguida.
        self._request("POST", "/session/connect",
                      json={"Subscribe": ["Message", "ReadReceipt"], "Immediate": True})
        return True

    def get_qr(self):
        data = self._request("GET", "/session/qr")
        qr = data.get("QRCode") or ""
        # WuzAPI devuelve "data:image/png;base64,XXXX"; el campo Binary de Odoo
        # quiere el base64 pelado.
        if qr.startswith("data:") and "," in qr:
            qr = qr.split(",", 1)[1]
        return qr or False

    def logout(self):
        self._request("POST", "/session/logout")
        return True

    def test_connection(self):
        st = self.status()
        if st != "connected":
            raise WhatsAppTransportError(
                "Sesión WuzAPI no conectada (estado: %s). Escaneá el QR." % st,
                failure_type="account")
        return True

    # ------------------------------------------------------------------ #
    #  Saliente
    # ------------------------------------------------------------------ #
    def send_text(self, number, body, reply_to_uid=None):
        payload = {"Phone": number, "Body": body}
        data = self._request("POST", "/chat/send/text", json=payload)
        return data.get("Id")

    def send_media(self, number, attachment, caption=None, reply_to_uid=None):
        b64 = attachment.datas
        if isinstance(b64, bytes):
            b64 = b64.decode()
        if not b64:
            b64 = base64.b64encode(attachment.raw or b"").decode()
        mime = attachment.mimetype or "application/octet-stream"
        data_uri = "data:%s;base64,%s" % (mime, b64)
        kind = mime.split("/")[0]
        if kind == "image":
            payload = {"Phone": number, "Image": data_uri}
            if caption:
                payload["Caption"] = caption
            endpoint = "/chat/send/image"
        elif kind == "video":
            payload = {"Phone": number, "Video": data_uri}
            if caption:
                payload["Caption"] = caption
            endpoint = "/chat/send/video"
        elif kind == "audio":
            payload = {"Phone": number, "Audio": data_uri}
            endpoint = "/chat/send/audio"
        else:
            payload = {"Phone": number, "Document": data_uri,
                       "FileName": attachment.name or "file"}
            endpoint = "/chat/send/document"
        data = self._request("POST", endpoint, json=payload)
        return data.get("Id")

    def send_reaction(self, number, target_uid, emoji):
        data = self._request("POST", "/chat/react",
                             json={"Phone": number, "Body": emoji, "Id": target_uid})
        return data.get("Id")

    def download_media(self, media_ref):
        # Con WuzAPI (skipmedia=false) la media entrante llega en base64 dentro del
        # webhook, así que normalmente no hace falta descargar aparte.
        # TODO(increment): /chat/downloadimage requiere Url+MediaKey+SHA+Length del
        # mensaje; implementar si se configura skipmedia=true.
        raise NotImplementedError("download_media: media llega inline por webhook")
