{
    'name': 'EuraTel Reports',
    'category': 'Report',
    'summary': 'Reports for EuraTel GmbH',
    'version': '1.0',
    'description': """
Reports for Euratel GmbH
        """,
    'author': 'artmin IT-Dienstleistungen',
    'depends': ['sale', 'base_phone', 'report', 'purchase_transport_multi_address', 'account_cash_discount_61'],
    'data': [
        'views/euratel_layout.xml',
        'views/euratel_invoice.xml',
        'views/res_company_view.xml',
        'views/amamedis_sales_order.xml',
        'views/amamedis_delivery_order.xml',
        'views/amamedis_purchase_order.xml',
        'views/sale_order_view.xml',
        'views/account_view.xml',
    ],
    'installable': True,
    'auto-install' : False,
}
