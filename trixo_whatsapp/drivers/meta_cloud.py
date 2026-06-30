# Part of Trixocom.
"""Driver del proveedor oficial: WhatsApp Cloud API (Meta / Graph API).

Implementación propia de Trixocom. La interfaz pública (Graph API) es pública y
puede replicarse; no se reutiliza código licenciado de Odoo Enterprise.
"""
import json
import logging
import mimetypes

import requests

from .base import WhatsAppTransport, WhatsAppTransportError, register_transport

_logger = logging.getLogger(__name__)

GRAPH_VERSION = "v23.0"
GRAPH_ENDPOINT = "https://graph.facebook.com/%s" % GRAPH_VERSION
TIMEOUT = (10, 30)


@register_transport
class MetaCloudTransport(WhatsAppTransport):
    provider = "meta_cloud"
    capabilities = frozenset({"templates", "media", "reactions"})

    # ------------------------------------------------------------------ #
    #  HTTP helper
    # ------------------------------------------------------------------ #
    def _request(self, method, path, *, params=None, headers=None, data=None,
                 files=None, absolute=False):
        token = self.account.sudo().meta_token
        phone_uid = self.account.meta_phone_uid
        if not (token and phone_uid):
            raise WhatsAppTransportError(
                "Cuenta Meta sin configurar (token / phone number id).",
                failure_type="account")
        url = path if absolute else (GRAPH_ENDPOINT + path)
        headers = dict(headers or {})
        headers.setdefault("Authorization", "Bearer %s" % token)
        try:
            res = requests.request(method, url, params=params, headers=headers,
                                   data=data, files=files, timeout=TIMEOUT)
        except requests.exceptions.RequestException as err:
            raise WhatsAppTransportError(str(err), failure_type="network") from err
        try:
            payload = res.json()
        except ValueError:
            if not res.ok:
                raise WhatsAppTransportError("HTTP %s" % res.status_code,
                                             failure_type="network")
            return res
        if isinstance(payload, dict) and payload.get("error"):
            err = payload["error"]
            raise WhatsAppTransportError(err.get("message", "Error Meta"),
                                         code=err.get("code"))
        return res

    # ------------------------------------------------------------------ #
    #  Saliente
    # ------------------------------------------------------------------ #
    def test_connection(self):
        account_uid = self.account.meta_account_uid
        res = self._request("GET", "/%s/phone_numbers" % account_uid)
        ids = [p["id"] for p in res.json().get("data", []) if "id" in p]
        if self.account.meta_phone_uid not in ids:
            raise WhatsAppTransportError("Phone Number ID inválido para esta cuenta.",
                                         failure_type="account")
        return True

    def _send(self, number, message_type, payload, reply_to_uid=None):
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": message_type,
            message_type: payload,
        }
        if reply_to_uid:
            data["context"] = {"message_id": reply_to_uid}
        res = self._request(
            "POST", "/%s/messages" % self.account.meta_phone_uid,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data))
        body = res.json()
        if body.get("messages"):
            return body["messages"][0]["id"]
        raise WhatsAppTransportError("Respuesta inesperada de Meta: %s" % body)

    def send_text(self, number, body, reply_to_uid=None):
        return self._send(number, "text", {"body": body, "preview_url": False},
                          reply_to_uid=reply_to_uid)

    def send_media(self, number, attachment, caption=None, reply_to_uid=None):
        media_id = self._upload_media(attachment)
        kind = (attachment.mimetype or "").split("/")[0]
        if kind not in ("image", "audio", "video"):
            kind = "document"
        payload = {"id": media_id}
        if caption and kind in ("image", "video", "document"):
            payload["caption"] = caption
        if kind == "document":
            payload["filename"] = attachment.name
        return self._send(number, kind, payload, reply_to_uid=reply_to_uid)

    def send_reaction(self, number, target_uid, emoji):
        return self._send(number, "reaction",
                          {"message_id": target_uid, "emoji": emoji})

    def _upload_media(self, attachment):
        files = [("file", (attachment.name, attachment.raw, attachment.mimetype))]
        res = self._request("POST", "/%s/media" % self.account.meta_phone_uid,
                            data={"messaging_product": "whatsapp"}, files=files)
        media_id = res.json().get("id")
        if not media_id:
            raise WhatsAppTransportError("Falló la subida de media a Meta.")
        return media_id

    def download_media(self, media_ref):
        res = self._request("GET", "/%s" % media_ref)
        file_url = res.json().get("url")
        return self._request("GET", file_url, absolute=True).content

    def send_template(self, number, template, variables):
        # TODO(increment-2): construir el payload de plantilla a partir de
        # whatsapp.template (components/lang) y enviarlo con type='template'.
        raise NotImplementedError("Plantillas Meta: pendiente increment 2")
