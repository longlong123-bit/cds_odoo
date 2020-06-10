# -*- coding: utf-8 -*-
{
    'name': 'Fill data',
    'version': '13.0.1',
    'category': 'Extra Tools',
    'summary': 'Button open search model data',
    'depends': ['base', 'web', 'account'],
    'data': [
        'views/assets.xml',
    ],
    'author': 'ToiTL',
    'demo': [],
    'qweb': [
            "static/src/xml/fill_data.xml",
            "static/src/xml/dialog.xml",
     ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}