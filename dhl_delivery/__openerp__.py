# -*- coding: utf-8 -*-
{
    'name': "DHL Versand",

    'summary': """
        Prepares DHL delivery slips for sending out deliveries.
        """,

    'description': """
        On the form view of the delivery orders a button is added which lets you
        create DHL delivery slips for this specific delivery. All created
        delivery slips are assigned to their delivery order.

        In a list view the status of the DHL deliveries can be monitored.
    """,

    'author': "artmin IT-Dienstleistungen",
    'website': "http://it.artmin.de",

    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['delivery'],

    # always loaded
    'data': [
        'views/dhl_delivery.xml',
        'security/ir.model.access.csv',
    ],
}
