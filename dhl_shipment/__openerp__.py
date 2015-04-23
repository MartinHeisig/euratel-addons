{
    'name': 'DHL Shipment',
    'category': 'Tools',
    'summary': 'Delivery through DHL',
    'version': '1.0',
    'description': """
Ermöglicht das Erstellen und Löschen von DHL Sendescheinen.
        """,
    'author': 'artmin IT-Dienstleistungen',
    'depends': ['stock'],
    'data': [
        'views/dhl_shipment_view.xml',
        'security/ir.model.access.csv',
        ],
    'installable': True,
    'auto-install' : False,
}
