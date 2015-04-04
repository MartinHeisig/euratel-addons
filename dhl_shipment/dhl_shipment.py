# -*- coding: utf-8 -*-
from openerp import models, fields, api
from datetime import date
from subprocess import Popen, PIPE
from openerp.exceptions import except_orm

# constants for creating arguments
RC_CONTACT_EMAIL = "Receiver_contact_email"
RC_CONTACT_NAME = "Receiver_contact_name"
RC_CONTACT_PHONE = "Receiver_contact_phone"
RC_COMPANY_NAME = "Receiver_company_name"
RC_FIRST_NAME = "Receiver_first_name"
RC_LAST_NAME = "Receiver_last_name"
RC_LOCAL_CITY = "Receiver_local_city"
RC_LOCAL_STREET = "Receiver_local_street"
RC_LOCAL_STREETNR = "Receiver_local_streetnr"
RC_LOCAL_ZIP = "Receiver_local_zip"
SHIPPING_NUMBER = "Shipping_number"
METHOD = "method"

class DHLShipment(models.Model):
  _name = 'stock.dhl.shipment'
  _description = "DHL Versand"

  # Columns
  delivery_slip = fields.Many2one('stock.picking', 'Lieferung')
  date = fields.Date('Datum')
  state = fields.Selection([ ('new','Neu'), ('pick_order_send', 'Abholung beauftragt'), ('deleted','Gelöscht')])
  shipment_id = fields.Char('Sendungsnummer')
  partner_id = fields.Many2one('res.partner', 'Lieferadresse')
  url = fields.Char('URL')

  # Show slip from tree view button
  @api.multi
  def show_slip(self):
    return {
      'type' : 'ir.actions.act_url',
      'url' : self.url,
      }

  def parseJavaOutput(self, out):
    splitted_output = out.split('\n')
    out_dict = {}
    for pair in splitted_output:
      splitted_pair = pair.split("=")
      out_dict[splitted_pair[0]] = splitted_pair[1]
    return out_dict

'''
Add dhl shipments to stock picking and provide function to create new shipment
orders at DHL.
'''
class StockDHLShipment(models.Model):
  _inherit = 'stock.picking'

  # Columns
  shipments = fields.One2many('stock.dhl.shipment', 'delivery_slip', string="DHL Sendungen")
  
  '''
  Converts a dictionary of the shipment arguments to a string using only the
  keys that have a value assigned to it.
  '''
  def _assamble_shipment_arguments(self, vals):
    res = ''
    for key, value in vals.iteritems():
      if value:
        res += key + '=\"' + value + '\" '
    return res

  '''
  Creates a new shipment object by assembling the necessary data and calling the
  java program which talks to the dhl api.
  '''
  @api.multi
  def create_shipment(self):
    # Assemble data for creating slip
    street_as_list = self.partner_id.street.split(' ')
    street = ' '.join(street_as_list[:-1])
    street_nr = street_as_list[-1]
    vals = {
            RC_CONTACT_EMAIL : self.partner_id.email,
            RC_CONTACT_PHONE : self.partner_id.phone,
            RC_COMPANY_NAME : self.partner_id.parent_id.name,
            RC_CONTACT_NAME : self.partner_id.parent_id.name,
            RC_FIRST_NAME : self.partner_id.first_name,
            RC_LAST_NAME : self.partner_id.name,
            RC_LOCAL_CITY : self.partner_id.city,
            RC_LOCAL_STREET: street,
            RC_LOCAL_STREETNR: street_nr,
            RC_LOCAL_ZIP: self.partner_id.zip,
            METHOD: "createShipment",
            }
    arguments = self._assamble_shipment_arguments(vals)
    # Call Java program
    out, err = Popen(["./dhl.jar", arguments], stdin=PIPE, stdout=PIPE,
            stderr=PIPE, cwd="/opt/dhl").communicate()
    # Raise error if we get content in stderr
    if err != '':
      raise except_orm('DHL Versand', err)
    # If no error occured create shipment
    else:
      out_dict = self.shipments.parseJavaOutput(out)
      # Check if label and shipment id for DHL shipment where returned
      if all (keys in out_dict for keys in ('label_url','shipment_number')):
        self.shipments.create({
          'delivery_slip' : self.id,
          'date' : date.today(),
          'state' : 'new',
          'shipment_id' : out_dict.get('shipment_number'),
          'partner_id' : self.partner_id.id,
          'url' : out_dict.get('label_url'),
          })
        # Open delivery slip
        return {
          'type' : 'ir.actions.act_url',
          'url' : out_dict.get('label_url'),
          }
      # Display status message from Java program if shipment could not be
      # created  
      else:
        raise except_orm('DHL Versand', out_dict.get(status_message))
    return
