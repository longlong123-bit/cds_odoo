# -*- coding: utf-8 -*-
{
    'name': "Bill Management - Draft Bill",
    'summary': """Manage bill""",
    'description': """
        Open Academy module for managing trainings:
            - training courses
            - training sessions
            - attendees registration
    """,

    'author': "SKcompany",
    'website': "https://www.skcompany.net",
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_setup',
        'sale',
        'Maintain_Bill_Management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/draft_bill.xml',
        'views/report_format.xml',
        'reports/reports.xml',
        'reports/normal_reports.xml',
        'reports/current_month_reports.xml',
        'reports/yamasa_invoice_reports.xml',
        'reports/abstract_payment_reports.xml',
        'reports/normal_invoice_for_earch_customer_report.xml',
        'reports/deposit_reports.xml',
        'reports/deposit_reports_1.xml',
    ],
    'qweb': [
        'static/src/xml/draft_bill_advanced_search.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
