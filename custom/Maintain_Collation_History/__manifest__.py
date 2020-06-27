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
        'base_setup', 'Maintain_Bill_Management', 'Maintain_Invoice_Remake',
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/collation_history.xml',
        'reports/collation_history_report.xml',
        'reports/report.xml',
    ],
    'qweb': [
        'static/src/xml/advanced_search.xml',
        'static/src/xml/bill_info_line.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
