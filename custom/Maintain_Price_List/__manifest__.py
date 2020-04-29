# -*- coding: utf-8 -*-
{
    'name': 'Price List',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Client', 'Maintain_Organization','product'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/price_list_custom_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

