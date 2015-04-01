# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 artmin - IT Dienstleistungen.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from openerp.osv import osv, fields
from openerp import tools, api

class amamedis_sales_team(osv.osv):

    _inherit = 'crm.case.section'
    _description = "Add custom fields for Amamedis sales team."
    
    @api.multi
    def _get_image(self, name, args):
        return dict((p.id, tools.image_get_resized_images(p.image)) for p in self)

    @api.one
    def _set_image(self, name, value, args):
        return self.write({'image': tools.image_resize_image_big(value)})

    _columns = {
            'from_email' : fields.char('Absenderemail', help="Emailadresse mit der Emails aus dem System versand werden."),
            'signature' : fields.html('Signatur', help="Signatur in Emails"),
            'from_line' : fields.char('Absenderzeile', help="Adresszeile für ausgehende Dokumente"),
            'footer' : fields.html('Fußzeile', help="Fußzeile für externe Dokumente"),
            'contact' : fields.html('Ansprechpartner', help="Ansprechpartner welche in ausgehenden Dokumenten angezeigt werden."),
            'closing' : fields.char('Briefabschluss'),
            'image' : fields.binary('Logo'),
            'image_medium' : fields.function(_get_image, fnct_inv=_set_image,
                string="Medium-sized image", type="binary", multi="_get_image",
                store={
                    'crm.case.section': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
                    },),
    }

class amamedis_sale_order(osv.osv):

    _inherit = 'sale.order'
    _description = "Add custom fields to sale order."

    _columns = {
            'delivery_date' : fields.char('Lieferdatum'),
            'client_order_date' : fields.date('Bestelldatum'),
            }
