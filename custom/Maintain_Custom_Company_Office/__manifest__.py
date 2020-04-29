# -*- coding: utf-8 -*-
{
    'name': 'Company Office',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'account'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/custom_company_office_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

