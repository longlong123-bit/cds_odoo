# -*- coding: utf-8 -*-
{
    'name': 'Invoice Print',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Client', 'Maintain_Organization', 'account'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        # 'views/add_js.xml',
        # 'views/invoice_print_view.xml',
        # 'views/report_view.xml',
        'views/report_invoice.xml',
        'views/report_format1.xml',
        'views/report_format2.xml',
        'views/report_format3.xml',
        'views/report_format4.xml',
        'views/report_shipment1.xml'
    ],
    'qweb': [
        'static/src/xml/report_template.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

