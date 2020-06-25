# -*- coding: utf-8 -*-
{
    'name': 'Quotation Reports',
    'version': '13.0',
    'author': 'TaiBX',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'sale_management', 'Maintain_Organization', 'Maintain_Client', 'account', 'Maintain_Quotations'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/menu.xml',
        'reports/handover_one.xml',
        'reports/normal_reports_1_in_1.xml',
        'reports/quotation_report_2.xml',
        'reports/quotation_report_3.xml',
        'reports/handover_three.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
