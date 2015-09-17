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

class answer(osv.osv):
  _inherit = "crm_profiling.answer"
  _columns = {
      "sequence" : fields.integer("Sequenz"),
      }
  _order = "sequence"

class question(osv.osv):
  _inherit = "crm_profiling.question"
  _columns = {
      "sequence" : fields.integer("Sequenz"),
      }
  _order = "sequence"

class partner(osv.osv):
  _inherit = "res.partner"
  _columns = {
      "profiling_remarks" : fields.text("Bemerkungen"),
      }
