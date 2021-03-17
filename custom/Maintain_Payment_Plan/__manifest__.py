# -*- coding: utf-8 -*-
{
    'name': 'Payment Plan',
    'version': '13.0',
    'author': 'TrongHuy',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'account', 'Maintain_Bill_Cancel', 'Maintain_Bill_Management',
        'Maintain_Collation_History', 'Maintain_Business_Partners_Remake'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/report_format.xml',
        'views/payment_plan.xml',
        'reports/payment_plan_report.xml',
    ],
    'qweb': [
        'static/src/xml/payment_request_bill_active.xml',
        'static/src/xml/payment_plan_advanced_search.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
