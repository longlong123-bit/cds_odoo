# -*- coding: utf-8 -*-
{
    'name': 'Supplier Ledger Inquiry',
    'version': '13.0',
    'author': 'NghiaNT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Invoice_Remake'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/supplier_ledger_inquiry_view.xml',
        'reports/report_supplier_ledger_inquiry.xml',
        'reports/report.xml',
    ],
    'qweb': [
        'static/src/xml/advanced_search.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

