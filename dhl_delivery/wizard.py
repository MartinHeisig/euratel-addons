# -*- coding: utf-8 -*-

from openerp import models, fields, api
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

class DHLStockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'
    
    # Fields
    create_dhl_delivery = fields.Boolean('DHL Paketversand', help="Dieses Kästchen "
        "aktivieren, wenn die Lieferung per DHL Paketversand vorgenommen wird.")
 
    '''
    Helper function that converts a dictionary of the shipment arguments to a string
    of arguments using only the keys that have a value assigned to it.
    '''
    # Should be removed when change to model is done
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
    # End should be removed

    
    '''
    Override method for sending a delivery to enable creating dhl deliveries
    '''
    @api.one
    def do_detailed_transfer(self):
        if self.create_dhl_delivery:
            parcels = 0
            sender = None
            # Get number of parcels to send
            for item in self.item_ids:
                if item.product_id.pcs_per_box != 0:
                    # Get sender address
                    if not sender:
                        sender = item.sourceloc_id.partner_id
                    quantity = float(item.quantity) / item.product_uom_id.factor
                    pcs_per_box = float(item.product_id.pcs_per_box) / item.product_id.uom_id.factor
                    parcels += int(ceil(quantity / pcs_per_box))
                else:
                     raise osv.except_osv(('Fehler'), ('Fuer das Produkt \"' +
                         item.product_id.name + '\" ist keine Gebindegröße hinterlegt.'))
            # Error handling
            if parcels == 0:
                raise osv.except_osv(('Fehler'), ('Die Anzahl der berechneten '
                    + 'Pakete ist null!'))
            if not sender:
                raise osv.except_osv(('Fehler'), ('Absender für die Pakete '
                    + ' konnte nicht gesetzt werden. Bitte Route waehlen, bzw.'
                    + ' Eigentuemer des Lagers setzen von dem Versand wird.'))
            if (sender.street == '' or sender.city == '' or sender.zip == ''):
                raise osv.except_osv(('DHL Versand'), ('Absendeadresse ' +
                    '(Eigentümer des Lagers) ist unvollständig.'))
            # Prepare call of Java tool
            # Divide street and street number for sender and reciever
            street_as_list = sender.street.split(' ')
            sh_street = ' '.join(street_as_list[:-1])
            sh_street_nr = street_as_list[-1]
            street_as_list = self.picking_id.partner_id.street.split(' ')
            rc_street = ' '.join(street_as_list[:-1])
            rc_street_nr = street_as_list[-1]
            company = self.picking_id.company_id
            # Set arguments
            vals = {
                    # Reciever details
                    RC_CONTACT_EMAIL : self.picking_id.partner_id.email,
                    RC_CONTACT_PHONE : self.picking_id.partner_id.phone,
                    RC_COMPANY_NAME : self.picking_id.partner_id.name,
                    RC_COMPANY_NAME_2 : self.picking_id.partner_id.first_name,
                    RC_LOCAL_CITY : self.picking_id.partner_id.city,
                    RC_LOCAL_STREET : rc_street,
                    RC_LOCAL_STREETNR : rc_street_nr,
                    RC_LOCAL_ZIP : self.picking_id.partner_id.zip,
                    NUMBER_OF_SHIPMENTS : str(parcels),
                    CUSTOMER_REFERENCE : self.picking_id.name,
                    # Sender details
                    SH_COMPANY_NAME : sender.name,
                    SH_STREET : sh_street,
                    SH_STREET_NR : sh_street_nr,
                    SH_CITY : sender.city,
                    SH_ZIP : sender.zip,
                    SH_CONTACT_EMAIL : sender.email,
                    SH_CONTACT_PHONE : sender.phone,
                    # Options and Credentials
                    METHOD : 'createShipment',
                    TEST : company.dhl_test and 'True' or False,
                    INTRASHIP_USER : company.dhl_intraship_user,
                    INTRASHIP_PASSWORD : company.dhl_intraship_password,
                    EKP : company.dhl_ekp,
                    PARTNER_ID : company.dhl_partner_id,
                    }
            arguments = self._assamble_shipment_arguments(vals)
            print arguments
            # Call Java program
            program_name = "./dhl.jar"
            command = ["java", "-jar", "./dhl.jar"]
            command.extend(arguments)
            out, err = Popen(command, stdin=PIPE, stdout=PIPE,
                    stderr=PIPE, cwd="/opt/dhl").communicate()
            # Raise error if we get content in stderr
            if err != '':
                raise osv.except_osv('DHL Versand - Java', err)             
            else:
                # Parse output from Java tool
                splitted_output = out.split('\n')
                # Open PDF for merging DHL delivery slips to one file
                pdf = PyPDF2.PdfFileMerger()
                for line in splitted_output:
                    # Get DHL deliveries
                    if '==' in line:
                        splitted_line = line.split("==")
                        shipment_number = splitted_line[0]
                        shipment_url = splitted_line[1]
                        # Create new dhl delivery object
                        dhl_delivery = self.env['dhl.delivery'].create({
                            'name' : shipment_number,
                            'delivery_order' : self.picking_id.id,
                            'url' : shipment_url,
                            })
                        # Assign dhl delivery to delivery order    
                        self.picking_id.dhl_deliveries |= dhl_delivery
                        # Download PDF and merge
                        path = "/opt/dhl/pdf/" + shipment_number + ".pdf"
                        try:
                            urllib.urlretrieve(shipment_url, path)
                            pdf.append(PyPDF2.PdfFileReader(path, 'rb'))
                        except:
                            raise osv.except_osv('DHL Versand',
                                'Konnte DHL Sendeschein nicht als PDF' +
                                'herunterladen. Ist das Verzeichnis /opt/dhl/pdf'
                                'fuer den odoo Benutzer schreibbar und ' +
                                'vorhanden?\nURL: ' + shipment_url)
                # Check for status message    
                    if '::' in line:
                        splitted_line = line.split("::")
                        status_code = splitted_line[0]
                        status_message = splitted_line[1]
                        if not status_code == '0':
                            raise osv.except_osv('DHL Versand - Java',
                                    status_message)
                # Close PDF file and save
                filename = self.picking_id.name + "-DHL.pdf"
                filename = filename.replace('/','_')
                path = "/opt/dhl/pdf/" + filename
                try: 
                    pdf.write(path)
                except:
                  raise osv.except_osv('DHL Versand',
                      'Konnte Sammelpdf nicht speicher\n' +
                      'Pfad: ' + path)
                
                # Also save pdf to synced owncloud directory
                if company.oc_local_dir:
                    if not company.oc_local_dir[:-1] == '/':
                      oc_path = company.oc_local_dir + '/'
                    else:
                      oc_path = company.oc_local_dir
                else:
                    raise osv.except_osv('DHL Versand Einstellungen',
                            'Bitte lokales owncloud Verzeichnis angeben.')
                # Get name of the year and supplier
                year = datetime.datetime.now().strftime('%Y')
                supplier = sender.name.replace(' ','_').replace('/','_')
                oc_path += year + '/' + supplier + '/DHL_Sendescheine/unversendet/'
                # Make directory if no existing
                try:
                    os.makedirs(oc_path) 
                except OSError as exception:
                    if exception.errno != errno.EEXIST:
                        raise osv.except_osv('DHL Versand',
                                'Konnte Verzeichnis nicht erstellen \''+ oc_path +
                                '\' schreiben.')
                if os.path.isdir(oc_path): 
                    # Write to owncloud directory
                    oc_path += filename
                    pdf.write(oc_path)
                    # Sync owncloud
                    command = ['owncloudcmd']
                    # Arguments
                    arguments = [
                            '-u', company.oc_user,
                            '-p', company.oc_password,
                            oc_path,
                            company.oc_remote_dir
                            ]
                    command.extend(arguments)
                    # Execute owncloud syncing
                    out, err = Popen(command, stdin=PIPE, stdout=PIPE,
                            stderr=PIPE).communicate()
                '''
                # Append pdf to self picking
                #with open(path, 'rb') as pdf_file:
                #    data = pdf_file.read()
                #    data = base64.encode(data)
                self.env['ir.attachment'].create({
                  'name' : filename,
                  'res_model' : 'stock.picking',
                  'res_id' : self.picking_id.id,
                  'description' : 'DHL Sendescheine Lieferung '
                                  + self.picking_id.name,
                  #'datas' : data,
                  })
                '''
           
        # Call super method
        super(DHLStockTransferDetails, self).do_detailed_transfer()
        return True
        
class DHLStockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    packaging_id = fields.Many2one('product.packaging', 'Verpackung')

