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

class euratel_partner(osv.osv):

    _inherit = 'res.partner'
    _description = "Add custom fields for Euratel partner."

    _columns = {
        'debit_ref': fields.char('Lastschrift Mandatsreferenz', size=64),
        'bga' : fields.char('BGA', size=64),
        'first_name' : fields.char('Vorname', size=64),
        'gender' : fields.selection((('w','weiblich'),('m','männlich')), 
                          'Geschlecht'),
    }
