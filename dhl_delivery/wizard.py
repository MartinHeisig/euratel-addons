# -*- coding: utf-8 -*-

from openerp import models, fields, api

class DHLWizard(models.TransientModel):
    _name = 'dhl.delivery.wizard'

    # Get delivery order from context
    def _default_delivery_order(self):
        return self.env['stock.picking'].browse(self._context.get('active_id'))

    def _default_parcel_weight(self):
        # get delivery order company and default values
        return 24.5

    # Fields
    delivery_order = fields.Many2one('stock.picking', string="Lieferung",
        required=True, default=_default_delivery_order)
    parcel_weight = fields.Float('Paketgewicht', default=_default_parcel_weight)

    @api.multi
    def create_deliveries(self):
        dhl_delivery = self.env['dhl.delivery'].create({'name': "Test",
          'delivery_order' : self.delivery_order.id })
        # Assign delivery order to delivery order    
        self.delivery_order.dhl_deliveries |= dhl_delivery
        return {}
        
