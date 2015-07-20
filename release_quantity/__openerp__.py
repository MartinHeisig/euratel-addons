# -*- coding: utf-8 -*-
{
    'name': "Abrufmengen",

    'summary': """
        Ermöglicht die Eingabe von Abrufmengen in Auftrag und Lieferung""",

    'description': """
        Erweitert die Auftragszeilen von Angebot bzw. Auftrag und von
        Lieferscheinen um das Feld Abrufmenge.
    """,

    'author': "artmin IT-Dienstleistungen",
    'website': "http://it.artmin.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'delivery',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale', 'delivery'],

    # always loaded
    'data': [
        'release_quantity_view.xml',
    ],
}
