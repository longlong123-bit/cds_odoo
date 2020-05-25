# -*- coding: utf-8 -*-
{
    'name': 'Quotation Print',
    'version': '13.0',
    'author': 'ToiTL',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'sale_management', 'Maintain_Organization', 'Maintain_Client'
    ],
    'website': '',
    'depends': ['product', 'sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/report_format1.xml',
        'views/menu.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
