# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
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

from openerp import api
from openerp import SUPERUSER_ID
from openerp.exceptions import AccessError
from openerp.osv import osv, fields
from openerp.tools import config
from openerp.tools.misc import find_in_path
from openerp.tools.translate import _
from openerp.addons.web.http import request
from openerp.tools.safe_eval import safe_eval as eval

import re
import time
import base64
import logging
import tempfile
import lxml.html
import os
import subprocess
from contextlib import closing
from distutils.version import LooseVersion
from functools import partial
from pyPdf import PdfFileWriter, PdfFileReader


#--------------------------------------------------------------------------
# Helpers
#--------------------------------------------------------------------------
_logger = logging.getLogger(__name__)


class Report(osv.Model):
    _inherit = "report"
    
    #--------------------------------------------------------------------------
    # Report generation helpers
    #--------------------------------------------------------------------------
    @api.v7
    def _check_attachment_use(self, cr, uid, ids, report):
        """ Check attachment_use field. If set to true and an existing pdf is already saved, load
        this one now. Else, mark save it.
        """
        save_in_attachment = {}
        save_in_attachment['model'] = report.model
        save_in_attachment['loaded_documents'] = {}

        if report.attachment:
            for record_id in ids:
                obj = self.pool[report.model].browse(cr, uid, record_id)
                filename = eval(report.attachment, {'object': obj, 'time': time})
                # filename = obj.name

                # If the user has checked 'Reload from Attachment'
                if report.attachment_use:
                    alreadyindb = [('datas_fname', '=', filename),
                                   ('res_model', '=', report.model),
                                   ('res_id', '=', record_id)]
                    attach_ids = self.pool['ir.attachment'].search(cr, uid, alreadyindb)
                    if attach_ids:
                        # Add the loaded pdf in the loaded_documents list
                        pdf = self.pool['ir.attachment'].browse(cr, uid, attach_ids[0]).datas
                        pdf = base64.decodestring(pdf)
                        save_in_attachment['loaded_documents'][record_id] = pdf
                        _logger.info('The PDF document %s was loaded from the database' % filename)

                        continue  # Do not save this document as we already ignore it

                # FIX START (commenting out below lines and indenting the else clause one level down)
                # If the user has checked 'Save as Attachment Prefix'
                # if filename is False:
                    # May be false if, for instance, the 'attachment' field contains a condition
                    # preventing to save the file.
                    # save_in_attachment[record_id] = obj.name
                    # continue
                    else:
                        save_in_attachment[record_id] = filename  # Mark current document to be saved
                # FIX END
        return save_in_attachment
