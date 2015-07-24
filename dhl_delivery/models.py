# -*- coding: utf-8 -*-

from openerp import models, fields, api

class DhlDelivery(models.Model):
    _name = 'dhl.delivery'

    name = fields.Char(string="Sendungsnummer", help="Diese Nummer wird auch für"
        "die Sendungsverfolgung verwendet.")
    delivery_order = fields.Many2one(comodel_name='stock.picking',
            ondelete='cascade', string="Lieferschein", delegate=True,
            required=True, domain=['|', ('state','=','partially_available'),
                         ('state','=','assigned')])
    state = fields.Selection([('new','Neu'), ('confirmed','Bestätigt'),
        ('delivery','In Zustellung'), ('delivered','Ausgeliefert'),
        ('deleted', 'Gelöscht')], default='new', readonly=True, string="Status")
    delivery_date = fields.Date(string="Zustelldatum",
        help="Tag an dem die Lieferung zugestellt wurde")

    # Add constraint to prevent duplicating deliveries
    _sql_constraints = [
            ('name_unique',
             'UNIQUE(name)',
             "DHL Sendungen können nicht dupliziert werden."),
            ]

    # Actions
    @api.one
    def action_delete(self):
        self.state = 'deleted'

class StockDhlDelivery(models.Model):
    _inherit = 'stock.picking'

    dhl_deliveries = fields.One2many(comodel_name='dhl.delivery',
            inverse_name='delivery_order', string="DHL Sendescheine")
