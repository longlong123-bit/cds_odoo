# -*- coding: utf-8 -*-
{
    'name': 'Collation History',
    'version': '13.0',
    'author': 'TaiBX',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Invoice_Remake',
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/collation_history.xml',
        # 'views/sequence.xml',
    ],
    'qweb': [
        'static/src/xml/advanced_search.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
