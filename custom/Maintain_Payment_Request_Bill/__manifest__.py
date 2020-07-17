# -*- coding: utf-8 -*-
{
    'name': 'Payment Request Bill',
    'version': '13.0',
    'author': 'TaiBX',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'account', 'Maintain_Bill_Cancel', 'Maintain_Invoice_Remake', 'Maintain_Bill_Management',
        'Maintain_Collation_History', 'Maintain_Business_Partners_Remake'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'reports/reports.xml',
        'reports/normal_reports.xml',
        'views/add_js.xml',
        'views/report_format.xml',
        'views/payment_request_bill.xml',
    ],
    'qweb': [
        'static/src/xml/payment_request_bill_active.xml',
        'static/src/xml/advanced_search.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
