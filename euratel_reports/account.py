# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning

class ama_account_payment_term(models.Model):
    _inherit = "account.payment.term"
    
    name_on_invoice = fields.Boolean('Name auf Rechnung', default=True, help='Bei gesetztem Haken erscheint zusaetzlich zu den Zeilen unten der Name der Zahlungsbedingung auf der Rechnung. Wenn abgewaehlt, dann nur die Zeilen unten.')


class ama_account_payment_term_line(models.Model):
    _inherit = "account.payment.term.line"

    report_text = fields.Char('Report-Text', required=True)