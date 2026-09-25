"""Campos que el vendedor restringido nunca ve (costo, margen).

No se bloquean por permiso de campo: en Odoo 19 un campo bloqueado que la
pantalla referencia (en un modificador, un widget o un botón) rompe la pantalla
entera. En cambio, para el vendedor restringido:
- el campo queda invisible en todas las vistas (también su etiqueta y la columna);
- cualquier lectura devuelve 0, también en totales y agrupados;
- la vista cacheada se distingue para él (la clave de caché de Odoo no incluye
  al usuario).
"""
from odoo import models


def restringido(model):
    return not model.env.su and model.env.user._trx_es_vendedor_restringido()


class OcultarCamposMixin(models.AbstractModel):
    _name = "trx.ocultar.campos.mixin"
    _description = "Oculta campos al vendedor restringido"

    _trx_campos_ocultos = ()

    def _trx_ocultos(self):
        return [f for f in self._trx_campos_ocultos if f in self._fields]

    def _read_format(self, fnames, load="_classic_read"):
        rows = super()._read_format(fnames, load)
        if restringido(self):
            ocultos = self._trx_ocultos()
            for row in rows:
                for fname in ocultos:
                    if fname in row:
                        row[fname] = 0.0
        return rows

    def _trx_anular_grupos(self, res):
        ocultos = self._trx_ocultos()
        pendientes = [res]
        while pendientes:
            item = pendientes.pop()
            if isinstance(item, list):
                pendientes.extend(item)
            elif isinstance(item, dict):
                for key in list(item):
                    if key.split(":")[0] in ocultos:
                        item[key] = 0.0
        return res

    def formatted_read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        res = super().formatted_read_group(domain, groupby, aggregates, having, offset, limit, order)
        return self._trx_anular_grupos(res) if restringido(self) else res

    def formatted_read_grouping_sets(self, domain, grouping_sets, aggregates=(), *, order=None):
        res = super().formatted_read_grouping_sets(domain, grouping_sets, aggregates, order=order)
        return self._trx_anular_grupos(res) if restringido(self) else res

    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if restringido(self):
            # por nombre, sin filtrar por modelo: la vista puede traer sub-vistas de
            # otro modelo (p.ej. las líneas dentro del formulario del pedido)
            nombres = list(self._trx_campos_ocultos)
            if nombres:
                cond = " or ".join("@name='%s'" % n for n in nombres)
                for node in arch.xpath("//field[%s]" % cond):
                    node.set("invisible", "1")
                    node.set("column_invisible", "1")
                    node.attrib.pop("optional", None)
                    padre = node.getparent()
                    if padre is not None and padre.tag == "div" and view_type == "form" and len(padre.xpath(".//field")) <= 2:
                        padre.set("invisible", "1")
                cond_label = " or ".join("@for='%s'" % n for n in nombres)
                for node in arch.xpath("//label[%s]" % cond_label):
                    node.set("invisible", "1")
        return arch, view

    def _get_view_cache_key(self, view_id=None, view_type="form", **options):
        return super()._get_view_cache_key(view_id, view_type, **options) + (restringido(self),)
