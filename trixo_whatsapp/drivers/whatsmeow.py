# Part of Trixocom.
"""Driver del proveedor whatsmeow (conexión directa por QR).

whatsmeow es una librería Go (``go.mau.fi/whatsmeow``, WhatsApp Web multidevice).
Como Odoo es Python, hablamos con un **sidecar** REST que embebe whatsmeow. El driver
trabaja contra el siguiente CONTRATO REST mínimo (que un adapter mapea a un wrapper
concreto como GOWA `go-whatsapp-web-multidevice` o WuzAPI):

    GET  {base}/session/status      -> {"status": "connected|qr_pending|logged_out"}
    POST {base}/session/connect     -> 200
    GET  {base}/session/qr          -> {"qr": "<base64 png>"}
    POST {base}/session/logout      -> 200
    POST {base}/messages/text       {"to","body","reply_to"}        -> {"id": "<uid>"}
    POST {base}/messages/media      multipart {"to","caption",file} -> {"id": "<uid>"}
    POST {base}/messages/reaction   {"to","target_id","emoji"}      -> {"id": "<uid>"}
    GET  {base}/media/{ref}                                          -> bytes

El sidecar empuja los mensajes entrantes a Odoo por webhook
``/trixo_whatsapp/whatsmeow/webhook`` (ver controllers/whatsmeow_webhook.py).

Riesgo: el canal directo viola los ToS de WhatsApp y puede derivar en baneo del
número. Decisión asumida por el cliente; documentado.
"""
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
            raise WhatsAppTransportError("Sidecar whatsmeow sin URL configurada.",
                                         failure_type="account")
        return base

    def _headers(self):
        headers = {}
        token = self.account.sudo().whatsmeow_token
        if token:
            headers["Authorization"] = "Bearer %s" % token
        sess = self.account.whatsmeow_session_id
        if sess:
            headers["X-Session-Id"] = sess
        return headers

    def _request(self, method, path, *, json=None, data=None, files=None):
        try:
            res = requests.request(method, self._base + path, json=json, data=data,
                                   files=files, headers=self._headers(), timeout=TIMEOUT)
        except requests.exceptions.RequestException as err:
            raise WhatsAppTransportError(str(err), failure_type="network") from err
        if not res.ok:
            raise WhatsAppTransportError("Sidecar HTTP %s: %s" %
                                         (res.status_code, res.text[:200]))
        return res

    # ------------------------------------------------------------------ #
    #  Sesión / QR
    # ------------------------------------------------------------------ #
    def status(self):
        try:
            return self._request("GET", "/session/status").json().get("status", "error")
        except WhatsAppTransportError:
            return "error"

    def connect(self):
        self._request("POST", "/session/connect")
        return True

    def get_qr(self):
        return self._request("GET", "/session/qr").json().get("qr")

    def logout(self):
        self._request("POST", "/session/logout")
        return True

    def test_connection(self):
        if self.status() != "connected":
            raise WhatsAppTransportError(
                "Sidecar whatsmeow no conectado (escaneá el QR).",
                failure_type="account")
        return True

    # ------------------------------------------------------------------ #
    #  Saliente
    # ------------------------------------------------------------------ #
    def send_text(self, number, body, reply_to_uid=None):
        res = self._request("POST", "/messages/text",
                            json={"to": number, "body": body, "reply_to": reply_to_uid})
        return res.json().get("id")

    def send_media(self, number, attachment, caption=None, reply_to_uid=None):
        files = [("file", (attachment.name, attachment.raw, attachment.mimetype))]
        res = self._request("POST", "/messages/media",
                            data={"to": number, "caption": caption or "",
                                  "reply_to": reply_to_uid or ""}, files=files)
        return res.json().get("id")

    def send_reaction(self, number, target_uid, emoji):
        res = self._request("POST", "/messages/reaction",
                            json={"to": number, "target_id": target_uid, "emoji": emoji})
        return res.json().get("id")

    def download_media(self, media_ref):
        return self._request("GET", "/media/%s" % media_ref).content
