# -*- coding: utf-8 -*-
# meine Änderungen

from openerp import models, fields, api
from openerp.osv import osv
from openerp.tools.translate import _
from math import ceil

from subprocess import Popen, PIPE
import urllib
import PyPDF2
import base64
import datetime
import os
import shutil
import errno
import logging

_logger = logging.getLogger(__name__)

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
          if value and value.strip() != '':
            # argument = [key + '=' + value.encode('utf-8').strip()]
            '''str(value).replace("ä", "ae")
            str(value).replace("ö", "oe")
            str(value).replace("ü", "ue")
            str(value).replace("Ä", "Ae")
            str(value).replace("Ö", "Oe")
            str(value).replace("Ü", "Ue")
            str(value).replace("ß", "ss")'''
            argument = [key + '=' + value.encode('iso-8859-1').strip()]
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
            # changed to sender all time amamedis
            # if need of single warehouse each time need to be fixed in the lines below because of no partner in source_loc while dropshipping
            sender = self.picking_id.company_id.partner_id
            
            # Get number of parcels to send
            for item in self.item_ids:
                if item.product_id.pcs_per_box != 0:
                    # Get sender address
                    if not sender:
                        if self.picking_id.picking_type_id and self.picking_id.picking_type_id.id == self.env['ir.model.data'].get_object_reference('stock_dropshipping', 'picking_type_dropship')[1]:
                            sender = self.picking_id.partner_id
                        else:
                            sender = item.sourceloc_id.partner_id
                    quantity = float(item.quantity) / item.product_uom_id.factor
                    pcs_per_box = float(item.product_id.pcs_per_box) / item.product_id.uom_id.factor
                    parcels += int(ceil(quantity / pcs_per_box))
                else:
                    if item.product_id.name:
                        raise osv.except_osv(('Fehler'), ('Fuer das Produkt \"' +
                            item.product_id.name.encode('utf-8') + '\" ist keine Gebindegröße hinterlegt.'))
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
            company = self.picking_id.company_id
            if not company.oc_local_dir:
                raise osv.except_osv('DHL Versand Einstellungen',
                            'Bitte lokales owncloud Verzeichnis angeben.')
                            
            receiver = self.picking_id.delivery_address_id
            # receiver = self.picking_id.move_lines[0].partner_id
            if not receiver:
                raise osv.except_osv(('Fehler'), ('Empfänger für die Pakete '
                    + ' konnte nicht gesetzt werden. Ursache: Lieferschein enthält keine Auftragszeilen oder diesen ist kein Empfänger zugeordnet.'))
            if (receiver.street == '' or receiver.city == '' or receiver.zip == ''):
                raise osv.except_osv(('DHL Versand'), ('Lieferadresse ist unvollständig.')) 

            # Prepare call of Java tool
            # Divide street and street number for sender and reciever
            try:
                if sender.street_name and sender.street_number:
                    sh_street = sender.street_name.strip()
                    sh_street_nr = sender.street_number.strip()
                else:
                    street_as_list = sender.street.split(' ')
                    sh_street = ' '.join(street_as_list[:-1]).strip()
                    sh_street_nr = street_as_list[-1].strip()
                if receiver.street_name and receiver.street_number:
                    rc_street = receiver.street_name.strip()
                    rc_street_nr = receiver.street_number.strip()
                else:
                    street_as_list = receiver.street.split(' ')
                    rc_street = ' '.join(street_as_list[:-1]).strip()
                    rc_street_nr = street_as_list[-1].strip()
            except:
                raise osv.except_osv(('Fehler'), ('Beim Auslesen und gegebenenfalls Aufsplitten trat ein Fehler auf. Möglicher Grund könnte sein, dass das Modul "partner_street_number", welches die Adresszeile in Straße und Hausnummer aufsplittet nicht installiert ist.'))
            company = self.picking_id.company_id
            
            # minimal first check for usage of DHL field lengths
            if receiver.name and len(receiver.name) > 30:
                raise osv.except_osv(('Fehler'), ('Feld Name beim Empfänger übersteigt die maximale Länge von 30 Zeichen'))
            if receiver.first_name and len(receiver.first_name) > 30:
                raise osv.except_osv(('Fehler'), ('Feld Vorname/Firmenzusatz beim Empfänger übersteigt die maximale Länge von 30 Zeichen'))
            if rc_street and len(rc_street) > 40:
                raise osv.except_osv(('Fehler'), ('Feld Strasse beim Empfänger übersteigt die maximale Länge von 40 Zeichen'))
            if rc_street_nr and len(rc_street_nr) > 7:
                # need to test with 10
                raise osv.except_osv(('Fehler'), ('Feld Hausnummer beim Empfänger übersteigt die maximale Länge von 7 Zeichen'))
            if receiver.zip and len(receiver.zip) > 5:
                # need to be raised to 10 for international shipment
                raise osv.except_osv(('Fehler'), ('Feld PLZ beim Empfänger übersteigt die maximale Länge von 5 Zeichen (da Deutschland voreingestellt)'))
            if receiver.city and len(receiver.city) > 50:
                # maybe only 20 based on use of district?
                raise osv.except_osv(('Fehler'), ('Feld Stadt beim Empfänger übersteigt die maximale Länge von 50 Zeichen'))
            if not receiver.is_company and not receiver.parent_id:
                # check if parent_id is set for a non company
                raise osv.except_osv(('Fehler'), ('Lieferadresse ist kein Unternehmen und ist auch keinem Unternehmen zugeordnet'))
            if not receiver.email and not receiver.phone:
                # one of them have to be set
                raise osv.except_osv(('Fehler'), ('Lieferkontakt hat weder E-Mail noch Telefonnummer. Eins davon muss aber mindestens gesetzt sein.'))
                
            if sender.name and len(sender.name) > 30:
                raise osv.except_osv(('Fehler'), ('Feld Name beim Sender übersteigt die maximale Länge von 30 Zeichen'))
            if sh_street and len(sh_street) > 40:
                raise osv.except_osv(('Fehler'), ('Feld Strasse beim Sender übersteigt die maximale Länge von 40 Zeichen'))
            if sh_street_nr and len(sh_street_nr) > 7:
                # need to test with 10
                raise osv.except_osv(('Fehler'), ('Feld Hausnummer beim Sender übersteigt die maximale Länge von 7 Zeichen'))
            if sender.zip and len(sender.zip) > 5:
                # need to be raised to 10 for intenational shipment
                raise osv.except_osv(('Fehler'), ('Feld PLZ beim Sender übersteigt die maximale Länge von 5 Zeichen (da Deutschland voreingestellt)'))
            if sender.city and len(sender.city) > 50:
                # maybe only 20 based on use of district?
                raise osv.except_osv(('Fehler'), ('Feld Stadt beim Sender übersteigt die maximale Länge von 50 Zeichen'))
            if not sender.email and not sender.phone:
                # one of them have to be set
                raise osv.except_osv(('Fehler'), ('Sender hat weder E-Mail noch Telefonnummer. Eins davon muss aber mindestens gesetzt sein.'))
            
            # Set arguments
            vals = {
                    # Receiver details
                    RC_CONTACT_EMAIL : receiver.email,
                    RC_CONTACT_PHONE : receiver.phone,
                    RC_COMPANY_NAME : receiver.is_company and receiver.name or receiver.parent_id.name,
                    RC_COMPANY_NAME_2 : receiver.is_company and receiver.first_name or not receiver.is_company and ' '.join([receiver.first_name or '', receiver.name or '']).strip(),
                    RC_LOCAL_CITY : receiver.city,
                    RC_LOCAL_STREET : rc_street,
                    RC_LOCAL_STREETNR : rc_street_nr,
                    RC_LOCAL_ZIP : receiver.zip,
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
            _logger.info("Anfrage nach Zusammenbau: " + str(vals))
            arguments = self._assamble_shipment_arguments(vals)
            _logger.info("Anfrage nach UTF-8 Kodierung: " + str(arguments))
            # print arguments
            # Call Java program
            program_name = "./dhl.jar"
            command = ["java", "-jar", "./dhl.jar"]
            command.extend(arguments)
            # _logger.info(str(command))
            out, err = Popen(command, stdin=PIPE, stdout=PIPE,
                    stderr=PIPE, cwd="/opt/dhl").communicate()
            # Raise error if we get content in stderr
            
            _logger.info("Antwort DHL wie sie aus JAVA kommt: " + str(out))
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
                            # uncomment after adding field url to the model
                            # 'url' : shipment_url,
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
                    res = {'warning': {
                                      'title': _('Warnung'),
                                      'message': _('Konnte Sammelpdf nicht speichern. Pfad: ' + path)
                                      }
                          }
                    return res
                # Add PDF as attachment to delivery note
                try:
                    attach_id = self.env['ir.attachment'].create({
                        'name':filename,
                        'datas_fname':filename,
                        'res_name': filename,
                        'type': 'binary',
                        'res_model': 'stock.picking',
                        'res_id': self.picking_id.id,
                        'datas': base64.b64encode(open(path, 'rb').read()),
                    })
                except:
                    res = {'warning': {
                                      'title': _('Warnung'),
                                      'message': _('Konnte PDF nicht als Attachment hinzufügen.')
                                      }
                          }
                    return res
                # Copy pdf to synced owncloud directory
                if not company.oc_local_dir[:-1] == '/':
                    oc_path = company.oc_local_dir + '/'
                else:
                    oc_path = company.oc_local_dir
                # Get name of the year and supplier name
                # year = datetime.datetime.now().strftime('%Y')
                # supplier = sender.name.replace(' ','_').replace('/','_')
                # oc_path += year + '/' + supplier + '/DHL_Sendescheine/unversendet/'
                # Make directory if not existing
                try:
                    # os.makedirs(oc_path)
                    os.makedirs(company.oc_local_dir)
                except OSError as exception:
                    if exception.errno != errno.EEXIST:
                        msg = 'Konnte Verzeichnis nicht erstellen \'' + oc_path
                        res = {'warning': {
                                            'title': _('Warnung'),
                                            'message': msg,
                                          }
                              }
                        return res
                # if os.path.isdir(oc_path):
                if os.path.isdir(company.oc_local_dir):
                    # Copy pdf to owncloud directory
                    shutil.copy(path, company.oc_local_dir)
                    # Sync owncloud
                    command = ['owncloudcmd']
                    # Arguments
                    arguments = [
                            '-u', company.oc_user,
                            '-p', company.oc_password,
                            company.oc_local_dir,
                            company.oc_remote_dir
                            ]
                    command.extend(arguments)
                    # Execute owncloud syncing
                    out, err = Popen(command, stdin=PIPE, stdout=PIPE,
                            stderr=PIPE).communicate()

        # Call super method
        super(DHLStockTransferDetails, self).do_detailed_transfer()
        return True

class DHLStockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    packaging_id = fields.Many2one('product.packaging', 'Verpackung')
