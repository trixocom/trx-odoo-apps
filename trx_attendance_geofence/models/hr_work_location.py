# -*- coding: utf-8 -*-
# Part of Trixocom. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    geofence_enabled = fields.Boolean(
        string="Geo-barreranactiva",
        help="Si está activa, los empleados asignados a esta ubicación solo "
             "pueden fichar (ingreso/egreso) desde el navegador o celular "
             "estando físicamente dentro del radio configurado.",
    )
    latitude = fields.Float(
        string="Latitud", digits=(10, 7),
        help="Latitud del punto de trabajo (ej: -34.6037232).",
    )
    longitude = fields.Float(
        string="Longitud", digits=(10, 7),
        help="Longitud del punto de trabajo (ej: -58.3815931).",
    )
    geofence_radius = fields.Integer(
        string="Radio de tolerancia (m)", default=100,
        help="Distancia máxima en metros al punto configurado dentro de la "
             "cual se permite fichar.",
    )

    @api.constrains('geofence_enabled', 'latitude', 'longitude', 'geofence_radius')
    def _check_geofence(self):
        for location in self:
            if not location.geofence_enabled:
                continue
            if not location.latitude or not location.longitude:
                raise ValidationError(_(
                    "La ubicación de trabajo «%(name)s» tiene la geo-barrera "
                    "activa pero no tiene latitud/longitud cargadas.",
                    name=location.name,
                ))
            if not (-90 <= location.latitude <= 90) or not (-180 <= location.longitude <= 180):
                raise ValidationError(_(
                    "Las coordenadas de «%(name)s» no son válidas "
                    "(latitud entre -90 y 90, longitud entre -180 y 180).",
                    name=location.name,
                ))
            if location.geofence_radius <= 0:
                raise ValidationError(_(
                    "El radio de tolerancia de «%(name)s» debe ser mayor a 0 metros.",
                    name=location.name,
                ))

    def action_open_map(self):
        """Abre el punto configurado en Google Maps para verificarlo."""
        self.ensure_one()
        if not self.latitude or not self.longitude:
            raise ValidationError(_("Cargá latitud y longitud antes de ver el mapa."))
        return {
            'type': 'ir.actions.act_url',
            'url': "https://maps.google.com?q=%s,%s" % (self.latitude, self.longitude),
            'target': 'new',
        }
