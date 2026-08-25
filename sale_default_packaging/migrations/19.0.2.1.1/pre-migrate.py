# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License LGPL-3


def migrate(cr, version):
    """Adopta el parametro stock_packaging_report.packaging_name que ya
    existe en bases migradas desde v18 (creado alli por stock_packaging_report
    o a mano), asignandole el xmlid de este modulo para que el data XML lo
    actualice en lugar de intentar crearlo (violaba ir_config_parameter_key_uniq).
    Idempotente."""
    cr.execute(
        """
        INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
        SELECT 'sale_default_packaging', 'config_default_packaging_name',
               'ir.config_parameter', icp.id, true
        FROM ir_config_parameter icp
        WHERE icp.key = 'stock_packaging_report.packaging_name'
          AND NOT EXISTS (
              SELECT 1 FROM ir_model_data
              WHERE module = 'sale_default_packaging'
                AND name = 'config_default_packaging_name'
          )
        """
    )
