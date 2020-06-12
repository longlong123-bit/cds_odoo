# -*- coding: utf-8 -*-
{
    'name': 'Accounts Receivable Balance List',
    'version': '13.0',
    'author': 'NghiaNT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'Maintain_Business_Partners_Remake',
        'Maintain_Custom_Common',
        'Maintain_Invoice_Remake'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/accounts_receivable_balance_list_view.xml',
        'report/report_accounts_receivable_balance_list.xml',
        'report/report.xml'
    ],
    'qweb': [
        'static/src/xml/advanced_search.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

