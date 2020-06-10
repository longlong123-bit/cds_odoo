# -*- coding: utf-8 -*-
{
    'name': 'Maintain_Widget_Quotation_History',
    'version': '13.0.1',
    'category': 'Extra Tools',
    'summary': 'Button open search quotation history',
    'depends': ['base', 'web', 'account'],
    'data': [
        'views/assets.xml',
    ],
    'author': 'ToiTL',
    'demo': [],
    'qweb': [
            "static/src/xml/refer2another.xml",
            "static/src/xml/dialog.xml",
     ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}