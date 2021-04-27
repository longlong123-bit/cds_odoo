# -*- coding: utf-8 -*-
{
    'name': 'Income Payment Custom',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    # 'depends': [
    #     'base_setup', 'sale_management', 'Maintain_Organization', 'Maintain_Client', 'Maintain_Widget_Billing_History'
    # ],
    'website': '',
    'depends': ['product', 'purchase', 'sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/income_payment_view.xml',
        'views/group_payment_master.xml',
        'views/many_payment_view.xml',
        'views/confirm_payment.xml',
        'views/report_payment.xml',
        'views/report_format1.xml',
    ],
    'qweb': [
        # "static/src/xml/history_payment.xml",
        'static/src/xml/advanced_search.xml',
        'static/src/xml/many_advanced_search.xml',
        'static/src/xml/dialog_advanced_search.xml',
        'static/src/xml/payment_line_advanced_search.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
