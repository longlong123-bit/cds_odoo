# -*- coding: utf-8 -*-
{
    'name': 'Maintain_Widget_Sale_History',
    'version': '13.0.1',
    'category': 'Extra Tools',
    'summary': 'Button open search sale history',
    'depends': ['base', 'web','account'],
    'data': [
        'views/assets.xml',
    ],
    'author': 'BinhDT',
    'demo': [],
    'qweb': [
            "static/src/xml/many2one_voucher_custom.xml",
            "static/src/xml/dialog_custom.xml",
     ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}