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
        'reports/invoice_normal_report.xml',
        'reports/invoice_normal_report2.xml',
        'reports/invoice_normal_report3.xml',
        'reports/invoice_reports.xml',
    ],
    'qweb': [
        'static/src/xml/report_template.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

