# Part of Trixocom.
"""Capa de abstracción de transporte WhatsApp.

Cada proveedor (Meta Cloud API, whatsmeow) implementa esta interfaz. El modelo
``whatsapp.account`` instancia el driver correspondiente vía ``_get_transport()`` y
todo el código de negocio (envío, recepción, Discuss) trabaja contra esta interfaz,
sin conocer el proveedor concreto.

Contrato del **evento entrante normalizado** que cada driver/controller debe producir
y entregar a ``whatsapp.account._process_inbound(event)``::

    {
        'msg_uid':      str,            # id único del mensaje en el proveedor
        'from':         str,            # número del remitente (E.164, sin '+')
        'sender_name':  str | None,     # nombre de perfil si está disponible
        'type':         str,            # text|image|document|audio|video|location|contacts|reaction
        'body':         str | None,     # texto / caption (ya en texto plano)
        'attachment':   (name, bytes, mimetype) | None,
        'reply_to_uid': str | None,     # msg_uid del mensaje citado, si es respuesta
        'reaction':     {'target_uid': str, 'emoji': str} | None,
        'raw':          dict,           # payload original del proveedor (debug)
    }
"""


class WhatsAppTransportError(Exception):
    """Error de transporte uniforme para todos los proveedores."""

    def __init__(self, message, code=None, failure_type=None):
        super().__init__(message)
        self.code = code
        self.failure_type = failure_type


class WhatsAppTransport:
    """Interfaz base. Subclasear por proveedor."""

    #: identificador del proveedor (coincide con la selección en whatsapp.account)
    provider = None
    #: capacidades declaradas: {'templates', 'qr', 'media', 'reactions'}
    capabilities = frozenset()

    def __init__(self, account):
        account.ensure_one()
        self.account = account

    def supports(self, capability):
        return capability in self.capabilities

    # ------------------------------------------------------------------ #
    #  Saliente
    # ------------------------------------------------------------------ #
    def test_connection(self):
        """Valida credenciales / sesión. Lanza WhatsAppTransportError si falla."""
        raise NotImplementedError

    def send_text(self, number, body, reply_to_uid=None):
        """Devuelve el msg_uid del mensaje enviado."""
        raise NotImplementedError

    def send_media(self, number, attachment, caption=None, reply_to_uid=None):
        """``attachment`` es un ir.attachment. Devuelve msg_uid."""
        raise NotImplementedError

    def send_reaction(self, number, target_uid, emoji):
        raise NotImplementedError

    def download_media(self, media_ref):
        """Descarga media entrante. Devuelve bytes."""
        raise NotImplementedError

    def fetch_avatar(self, number):
        """Devuelve los bytes de la foto de perfil del contacto, o b'' si no hay."""
        return b""

    def fetch_group_name(self, group_jid):
        """Devuelve el nombre (subject) de un grupo, o None."""
        return None

    # ------------------------------------------------------------------ #
    #  Plantillas (sólo proveedores que las soporten, p.ej. Meta)
    # ------------------------------------------------------------------ #
    def send_template(self, number, template, variables):
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    #  Sesión interactiva (sólo proveedores con login por QR, p.ej. whatsmeow)
    # ------------------------------------------------------------------ #
    def connect(self):
        raise NotImplementedError

    def get_qr(self):
        """Devuelve el QR de login (str/base64) o None si ya está conectado."""
        raise NotImplementedError

    def logout(self):
        raise NotImplementedError

    def status(self):
        """Devuelve uno de: 'connected' | 'qr_pending' | 'logged_out' | 'error'."""
        raise NotImplementedError


#: registro proveedor -> clase de transporte (lo pueblan los módulos de driver)
TRANSPORT_REGISTRY = {}


def register_transport(cls):
    """Decorator para registrar una implementación de transporte."""
    if not cls.provider:
        raise ValueError("El transporte %r no define 'provider'" % cls)
    TRANSPORT_REGISTRY[cls.provider] = cls
    return cls
