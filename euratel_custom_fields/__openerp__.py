{
    'name': 'EuraTel Custom Fields',
    'category': 'Tools',
    'summary': 'Custom fields for EuraTel GmbH',
    'version': '1.0',
    'description': """
Benutzerdefiniert Felder für Euratel GmbH
Kundenansicht:
* Lastschrift Mandatsreferenz
* BGA
        """,
    'author': 'artmin IT-Dienstleistungen',
    'depends': ['sale'],
    'data': [
        'views/partner_view.xml',
    ],
    'installable': True,
    'auto-install' : False,
}
