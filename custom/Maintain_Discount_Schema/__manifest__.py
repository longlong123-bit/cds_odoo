# -*- coding: utf-8 -*-
{
    'name': 'Discount Schema',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Client', 'Maintain_Organization'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/discount_schema_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

