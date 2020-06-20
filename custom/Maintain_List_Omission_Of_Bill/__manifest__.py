# -*- coding: utf-8 -*-
{
    'name': 'List Omission Of Bill',
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
        'views/list_omission_of_bill_view.xml',
        'report/report_list_omission_of_bill.xml',
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

