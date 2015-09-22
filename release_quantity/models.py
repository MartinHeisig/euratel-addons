# -*- coding: utf-8 -*-

from openerp import models, fields, api

class SaleOrderLineReleaseQuantity(models.Model):
    _inherit = 'sale.order.line'

    release_quantity = fields.Float('Abrufmenge',
      help="Anzahl der Produkte für einzelnen Lagerabrufe in der gleichen "
           "Einheit, wie die Standardmengeneinheit.")

class MoveLineReleaseQuantity(models.Model):
    _inherit = 'stock.move'

    release_quantity = fields.Float('Abrufmenge',
      help="Anzahl der Produkte für einzelnen Lagerabrufe in der gleichen "
           "Einheit, wie die Standardmengeneinheit.")
