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
        'first_name' : fields.char('Vorname / Firmenname Zusatz', size=64),
        'gender' : fields.selection((('w','weiblich'),('m','männlich')), 
                          'Geschlecht'),
        'branch_ids' : fields.many2many(
            'res.partner',
            'res_partner_branch',
            'partner_id',
            'branch_id',
            'Filialen'),
    }

    ''' Adds city to all displays of partners and gives possibility to show city
    in many2one relation. '''
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if record.parent_id and not record.is_company:
                name = "%s, %s" % (record.parent_name, name)
            if record.city:
                name += ' (' + record.city + ')'
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_street') and record.street:
                name += "\n" + record.street
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res
