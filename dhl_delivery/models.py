# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import except_orm

from openerp.osv import osv
from math import ceil

from subprocess import Popen, PIPE
import urllib
import PyPDF2
import base64
import datetime
import os
import errno

from constants import *


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

    '''
    Helper function that converts a dictionary of the shipment arguments to a string
    of arguments using only the keys that have a value assigned to it.
    '''
    def _assamble_shipment_arguments(self, vals):
        res = []
        for key, value in vals.iteritems():
          if value:
            argument = [key + '=' + value]
            res.extend(argument)
        return res

    def _parseJavaOutput(self, out):
        splitted_output = out.split('\n')
        out_dict = {}
        for pair in splitted_output:
          if '==' in pair:
            splitted_pair = pair.split("==")
            out_dict[splitted_pair[0]] = splitted_pair[1]
        return out_dict

    # Override delete method, so that shipment is deleted at DHL too.
    @api.one
    def unlink(self):
        # First call java function to delete delivery slip at DHL
        self.action_delete()
        # If no error occured delete shipment
        super(DhlDelivery, self).unlink()
        return
 
    # Actions
    @api.one
    def action_delete(self):
        if self.name:
            # Check if sandbox is active
            test = self.delivery_order.company_id.dhl_test and TEST + '=True' or ''
            # Delete shipment at DHL -  Call Java program
            command = ["java", "-jar", "./dhl.jar"]
            # Add arguments
            arguments = [ METHOD + "=deleteShipment",
                    SHIPPING_NUMBER + "=" + self.name,
                    test]
            command.extend(arguments)
            out, err = Popen(command, stdin=PIPE, stdout=PIPE,
                    stderr=PIPE, cwd="/opt/dhl").communicate()
            # Raise error if we get content in stderr
            if err != '':
                raise except_orm('DHL Versand', err)
                return
        self.state = 'deleted'
        return

    '''
    TODO !
    Override create method so that DHL deliveries can be created through dhl
    api.
    @api.one
    def create(self, vals):
        picking_id = vals.get('picking_id')
        # Handle single delivery slip creation
        if not 'shipper' in vals:
            # Get first line of picking
            if len(picking_id.

        super(DhlDelivery, self).create()
    '''

class StockDhlDelivery(models.Model):
    _inherit = 'stock.picking'

    dhl_deliveries = fields.One2many(comodel_name='dhl.delivery',
            inverse_name='delivery_order', string="DHL Sendescheine")

class CompanyDhlDelivery(models.Model):
    _inherit = 'res.company'
    # DHL parameters
    dhl_ekp = fields.Char('EKP', size=10,
            help="Einheitliche Kunden- und Produktnummer.")
    dhl_partner_id = fields.Char('Partner ID', size=2,
            help="Teilnehmernummer")
    dhl_intraship_user = fields.Char('Intraship Benutzername')
    dhl_intraship_password = fields.Char('Intraship Passwort')
    dhl_test = fields.Boolean('Testbetrieb', 
            help="Lässt alle DHL Abläufe im Testbetrieb laufen. "
            "Es werden keine echten Versandscheine erzeugt.")
    # Owncloud Login and directories
    oc_user = fields.Char('Benutzername')
    oc_password = fields.Char('Passwort')
    oc_local_dir = fields.Char('Lokales Verzeichnis')
    oc_remote_dir = fields.Char('Entferntes Verzeichnis')

class ProductDhlDelivery(models.Model):
    _inherit = 'product.template'

    pcs_per_box = fields.Float('Gebindegröße',
            help="Anzahl der Produkte, die in ein Paket passen. "
            "Menge wird in der Standardmengeneinheit angegeben.")
