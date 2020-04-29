# -*- coding: utf-8 -*-
{
    'name': 'Organization',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Client'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/organization_custom.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': True
}

