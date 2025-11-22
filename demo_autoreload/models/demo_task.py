# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DemoTask(models.Model):
    """
    Modelo de ejemplo para demostrar auto-reload.
    
    Prueba modificando este archivo mientras Odoo está corriendo:
    1. Agrega un nuevo campo
    2. Modifica el método compute
    3. Agrega validaciones
    4. Los cambios se aplicarán automáticamente (verás el reload en los logs)
    """
    _name = 'demo.task'
    _description = 'Tarea de Demostración'
    _order = 'priority desc, id desc'
    
    # Campos básicos
    name = fields.Char(
        string='Título',
        required=True,
        help='Nombre de la tarea'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada de la tarea'
    )
    
    # Campo de selección
    priority = fields.Selection(
        selection=[
            ('0', 'Baja'),
            ('1', 'Normal'),
            ('2', 'Alta'),
            ('3', 'Urgente'),
        ],
        string='Prioridad',
        default='1',
        help='Nivel de prioridad de la tarea'
    )
    
    # Campo de estado
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('in_progress', 'En Progreso'),
            ('done', 'Completada'),
            ('cancelled', 'Cancelada'),
        ],
        string='Estado',
        default='draft',
        tracking=True,
        help='Estado actual de la tarea'
    )
    
    # Campos de fecha
    date_start = fields.Date(
        string='Fecha Inicio',
        default=fields.Date.today,
        help='Fecha de inicio de la tarea'
    )
    
    date_end = fields.Date(
        string='Fecha Fin',
        help='Fecha de finalización de la tarea'
    )
    
    # Campo many2one
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        help='Usuario responsable de la tarea'
    )
    
    # Campo booleano
    is_urgent = fields.Boolean(
        string='¿Es Urgente?',
        compute='_compute_is_urgent',
        store=True,
        help='Indica si la tarea es urgente'
    )
    
    # Campo computado
    progress = fields.Float(
        string='Progreso (%)',
        default=0.0,
        help='Porcentaje de progreso de la tarea'
    )
    
    # Campo computado de días restantes
    days_remaining = fields.Integer(
        string='Días Restantes',
        compute='_compute_days_remaining',
        help='Número de días hasta la fecha de finalización'
    )
    
    # Campos de auditoría
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, la tarea estará archivada'
    )
    
    # Campo de notas
    notes = fields.Html(
        string='Notas',
        help='Notas adicionales sobre la tarea'
    )
    
    # =============================
    # MÉTODOS COMPUTADOS
    # =============================
    
    @api.depends('priority')
    def _compute_is_urgent(self):
        """
        Calcula si la tarea es urgente basándose en la prioridad.
        
        Prueba cambiando la lógica aquí y verás el cambio inmediato.
        """
        for record in self:
            record.is_urgent = record.priority in ['2', '3']
    
    @api.depends('date_end')
    def _compute_days_remaining(self):
        """
        Calcula los días restantes hasta la fecha de finalización.
        """
        today = fields.Date.today()
        for record in self:
            if record.date_end:
                delta = record.date_end - today
                record.days_remaining = delta.days
            else:
                record.days_remaining = 0
    
    # =============================
    # CONSTRAINTS
    # =============================
    
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """
        Valida que la fecha de inicio no sea posterior a la fecha de fin.
        """
        for record in self:
            if record.date_start and record.date_end:
                if record.date_start > record.date_end:
                    raise ValidationError(
                        'La fecha de inicio no puede ser posterior a la fecha de fin.'
                    )
    
    @api.constrains('progress')
    def _check_progress(self):
        """
        Valida que el progreso esté entre 0 y 100.
        """
        for record in self:
            if not 0 <= record.progress <= 100:
                raise ValidationError(
                    'El progreso debe estar entre 0 y 100.'
                )
    
    # =============================
    # MÉTODOS DE ACCIÓN
    # =============================
    
    def action_start(self):
        """
        Inicia la tarea.
        """
        for record in self:
            record.state = 'in_progress'
            if not record.date_start:
                record.date_start = fields.Date.today()
    
    def action_complete(self):
        """
        Marca la tarea como completada.
        """
        for record in self:
            record.state = 'done'
            record.progress = 100.0
            if not record.date_end:
                record.date_end = fields.Date.today()
    
    def action_cancel(self):
        """
        Cancela la tarea.
        """
        for record in self:
            record.state = 'cancelled'
    
    def action_reset_to_draft(self):
        """
        Resetea la tarea a borrador.
        """
        for record in self:
            record.state = 'draft'
            record.progress = 0.0
    
    # =============================
    # MÉTODOS OVERRIDE
    # =============================
    
    @api.model
    def create(self, vals):
        """
        Override del método create para agregar lógica personalizada.
        """
        # Aquí puedes agregar lógica adicional
        record = super(DemoTask, self).create(vals)
        
        # Ejemplo: Log de creación
        # import logging
        # _logger = logging.getLogger(__name__)
        # _logger.info(f'Nueva tarea creada: {record.name}')
        
        return record
    
    def write(self, vals):
        """
        Override del método write para agregar lógica personalizada.
        """
        # Aquí puedes agregar lógica adicional
        result = super(DemoTask, self).write(vals)
        
        # Ejemplo: Actualizar fecha de fin automáticamente al completar
        if 'state' in vals and vals['state'] == 'done':
            for record in self:
                if not record.date_end:
                    record.date_end = fields.Date.today()
        
        return result
    
    def unlink(self):
        """
        Override del método unlink para agregar lógica personalizada.
        """
        # Validar antes de eliminar
        for record in self:
            if record.state == 'in_progress':
                raise ValidationError(
                    'No puedes eliminar una tarea que está en progreso. '
                    'Primero cancélala o completala.'
                )
        
        return super(DemoTask, self).unlink()
    
    # =============================
    # MÉTODOS ÚTILES
    # =============================
    
    def name_get(self):
        """
        Override del name_get para personalizar cómo se muestra el registro.
        """
        result = []
        for record in self:
            priority_symbol = '🔴' if record.priority in ['2', '3'] else '⚪'
            name = f"{priority_symbol} {record.name}"
            result.append((record.id, name))
        return result


# =============================================================================
# INSTRUCCIONES PARA PROBAR AUTO-RELOAD:
# =============================================================================
#
# 1. Instala el módulo "Demo Auto-Reload"
# 2. Abre el menú "Demo Tasks"
# 3. Deja abierta una terminal con: docker-compose logs -f odoo
# 4. Modifica este archivo, por ejemplo:
#    - Agrega un nuevo campo después de 'notes':
#      test_field = fields.Char(string='Campo de Prueba')
#    - Guarda el archivo
#    - Verás en los logs: "odoo.modules.loading: Reloading ..."
# 5. Actualiza la página del navegador (F5)
# 6. Ve a Configuración > Base de Datos > Actualizar Aplicaciones
# 7. Selecciona "Demo Auto-Reload" y haz clic en Actualizar
# 8. ¡El nuevo campo aparecerá en la vista!
#
# NOTA: Para cambios en XML (vistas), necesitas actualizar el módulo.
#       Para cambios en Python, el auto-reload los detecta automáticamente.
# =============================================================================
