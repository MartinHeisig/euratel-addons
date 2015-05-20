# -*- coding: utf-8 -*-
from openerp import models, fields, api
from datetime import date
from subprocess import Popen, PIPE
from openerp.exceptions import except_orm
import urllib

# constants for creating arguments

# Sender
SH_COMPANY_NAME = "Shipper_company_name";
SH_STREET = "Shipper_street";
SH_STREET_NR = "Shipper_street_nr";
SH_CITY = "Shipper_city";
SH_ZIP = "Shipper_zip";
SH_CONTACT_EMAIL = "Shipper_contact_email";
SH_CONTACT_NAME = "Shipper_contact_name";
SH_CONTACT_PHONE = "Shipper_contact_phone";

# Receiver
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
NUMBER_OF_SHIPMENTS = "Number_of_shipments"

# Other
SHIPPING_NUMBER = "Shipping_number"
METHOD = "Method"
TEST = "Test"

# Credentials
EKP = "EKP"
PARTNER_ID = "Partner_ID"

class DHLShipment(models.Model):
  _name = 'stock.dhl.shipment'
  _description = "DHL Versand"

  # Columns
  delivery_slip = fields.Many2one('stock.picking', 'Lieferung')
  date = fields.Date('Datum')
  state = fields.Selection([ ('new','Neu'), ('pick_order_send', 'Abholung beauftragt'),
      ('deleted','Gelöscht')], default='new')
  name = fields.Char('Sendungsnummer')
  partner_id = fields.Many2one('res.partner', 'Lieferadresse')
  url = fields.Char('URL')

  def _parseJavaOutput(self, out):
    splitted_output = out.split('\n')
    out_dict = {}
    for pair in splitted_output:
      if '==' in pair:
        splitted_pair = pair.split("==")
        out_dict[splitted_pair[0]] = splitted_pair[1]
    return out_dict

  # When user selects the delivery slip in the form view ->
  # get the associated partner
  @api.onchange('delivery_slip')
  def _set_partner_from_delivery_slip(self):
    self.partner_id = self.delivery_slip.partner_id
    return
  
  # Override delete method, so that shipment is deleted at DHL too.
  @api.one
  def unlink(self):
    if self.name:
      # Delete shipment at DHL -  Call Java program
      command = ["java", "-jar", "./dhl.jar"]
      # Add arguments
      arguments = [ METHOD + "=deleteShipment",
              SHIPPING_NUMBER + "=" + shipment.name ]
      command.extend(arguments)
      out, err = Popen(command, stdin=PIPE, stdout=PIPE,
              stderr=PIPE, cwd="/opt/dhl").communicate()
      # Raise error if we get content in stderr
      if err != '':
        raise except_orm('DHL Versand', err)
        return
    # If no error occured delete shipment
    super(DHLShipment, self).unlink()
    return
     
  '''
  Converts a dictionary of the shipment arguments to a string using only the
  keys that have a value assigned to it.
  '''
  def _assamble_shipment_arguments(self, vals):
    res = []
    for key, value in vals.iteritems():
      if value:
        argument = [key + '=' + value]
        res.extend(argument)
    return res


  '''
  Creates a new shipment object by assembling the necessary data and calling the
  java program which talks to the dhl api.
  '''
  @api.multi
  def create_shipment(self, delivery_slip):
    # Assemble data for creating slip
    street_as_list = delivery_slip.partner_id.street.split(' ')
    street = ' '.join(street_as_list[:-1])
    street_nr = street_as_list[-1]
    vals = {
            RC_CONTACT_EMAIL : delivery_slip.partner_id.email,
            RC_CONTACT_PHONE : delivery_slip.partner_id.phone,
            RC_COMPANY_NAME : delivery_slip.partner_id.parent_id.name,
            RC_CONTACT_NAME : delivery_slip.partner_id.parent_id.name,
            RC_FIRST_NAME : delivery_slip.partner_id.first_name,
            RC_LAST_NAME : delivery_slip.partner_id.name,
            RC_LOCAL_CITY : delivery_slip.partner_id.city,
            RC_LOCAL_STREET: street,
            RC_LOCAL_STREETNR: street_nr,
            RC_LOCAL_ZIP: delivery_slip.partner_id.zip,
            # SH_COMPANY_NAME : delivery_slip.
            METHOD: "createShipment",
            }
    arguments = self._assamble_shipment_arguments(vals)
    # Call Java program
    program_name = "./dhl.jar"
    command = [program_name]
    command.extend(arguments)
    out, err = Popen(command, stdin=PIPE, stdout=PIPE,
            stderr=PIPE, cwd="/opt/dhl").communicate()
    # Raise error if we get content in stderr
    if err != '':
      raise except_orm('DHL Versand', err)
    # If no error occured create shipment
    else:
      out_dict = self._parseJavaOutput(out)
      # Check status
      if out_dict.get('status_code') == "0":
        super(DHLShipment, self).create({
          'delivery_slip' : delivery_slip.id,
          'date' : date.today(),
          'state' : 'new',
          'name' : out_dict.get('shipment_number'),
          'partner_id' : delivery_slip.partner_id.id,
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

  '''
  Is called when shipment is initialized from form view.
  '''
  @api.one
  def create(self):
    raise except_orm('DHL Versand', 'Sendescheine können nur von Lieferscheinen aus angelegt werden')
    return

'''
Add dhl shipments to stock picking and provide function to create new shipment
orders at DHL.
'''
class StockDHLShipment(models.Model):
  _inherit = 'stock.picking'

  # Columns
  shipments = fields.One2many('stock.dhl.shipment', 'delivery_slip',
                              string="DHL Sendungen", ondelete="cascade")
  
  @api.multi
  def create_shipment(self):
    return self.shipments.create_shipment(self)

class StockMove(models.Model):
  _inherit = 'stock.move'

  # Columns
  supplier_ref = fields.Char(string="Auftragsnr.", help="Auftragsnummer desLieferanten")

'''
This class is used to create several delivery slips for selected delivery orders
'''
class DHLShipmentCreate(models.Model):
  _name = 'stock.dhl.shipment.create'

  # Columns
  weight = fields.Float(string="Paketgewicht", default="24.0")
  shipments = fields.Many2many('stock.picking', string="Lieferschein")
  
  # Create several dhl shipment slips according to weight of delivery order
  def createShipment(self):
    return
