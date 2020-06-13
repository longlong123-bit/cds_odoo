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
        'base_setup', 'account', 'Maintain_Bill_Cancel',
    ],
    'website': '',
    'data': [
        'views/add_js.xml',
        'security/ir.model.access.csv',
        'views/payment_request_template.xml',
        'views/payment_request_template_custom.xml',
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
