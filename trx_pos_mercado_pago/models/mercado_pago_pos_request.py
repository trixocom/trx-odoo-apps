# Derivado de odoo/odoo master addons/pos_mercado_pago (LGPL-3), adaptado a Odoo 19 por Trixocom.
import logging
import uuid

import requests
from odoo import _

_logger = logging.getLogger(__name__)


REQUEST_TIMEOUT = 10
MERCADO_PAGO_API_ENDPOINT = 'https://api.mercadopago.com'

# No es secreto: identifica a Odoo como integrador para que Mercado Pago
# cuantifique usuarios de Odoo. Va en el body de la order en `integration_data`.
MERCADO_PAGO_PLATFORM_ID = "dev_cdf1cfac242111ef9fdebe8d845d0987"


class MercadoPagoPosRequest:
    def __init__(self, mp_bearer_token):
        self.mercado_pago_bearer_token = mp_bearer_token

    def call_mercado_pago(self, method, endpoint, payload, idempotent=False):
        """ Llamada a la API de Mercado Pago.

        :param method: "GET", "POST", ...
        :param endpoint: path del endpoint.
        :param payload: body JSON.
        :param idempotent: si True agrega X-Idempotency-Key (obligatorio en la
            Orders API para POST /v1/orders y .../refund).
        :return: dict con el JSON de la respuesta (o {'errorMessage': ...}).
        """
        endpoint = MERCADO_PAGO_API_ENDPOINT + endpoint
        header = {
            'Authorization': f"Bearer {self.mercado_pago_bearer_token}",
        }
        if idempotent:
            header['X-Idempotency-Key'] = str(uuid.uuid4())
        try:
            response = requests.request(method, endpoint, headers=header, json=payload, timeout=REQUEST_TIMEOUT)
            # Algunos endpoints (p.ej. POST /v1/orders/{id}/events) devuelven 204 sin body.
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()
        except requests.exceptions.RequestException as error:
            _logger.warning("Cannot connect with Mercado Pago POS. Error: %s", error)
            return {'errorMessage': str(error)}
        except ValueError as error:
            _logger.warning("Cannot decode response json. Error: %s", error)
            return {'errorMessage': _("Cannot decode Mercado Pago POS response. Error: %s", error)}
