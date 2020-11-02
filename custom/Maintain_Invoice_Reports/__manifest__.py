# -*- coding: utf-8 -*-

{
    'name': 'Invoice Reports Template',
    'version': '13.0',
    'author': 'TaiBX',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Client', 'Maintain_Organization', 'account', 'Maintain_Invoice_Remake'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/report_invoice.xml',
        'views/view_report_invoice_confirmation.xml',
        'reports/invoice_normal_report.xml',
        'reports/invoice_normal_report2.xml',
        'reports/invoice_normal_report3.xml',
        'reports/invoice_normal_report4.xml',
        'reports/invoice_confirmation_report.xml',
        'reports/invoice_reports.xml',
        'reports/confirmation_reports.xml',
        'reports/normal_report_confirm.xml',
        'reports/new_invoice_normal_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
