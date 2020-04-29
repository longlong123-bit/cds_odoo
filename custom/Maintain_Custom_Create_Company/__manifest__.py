# -*- coding: utf-8 -*-
{
    'name': 'Custom Company',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'base', 'account'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/custom_create_company_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

