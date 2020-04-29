# -*- coding: utf-8 -*-
{
    'name': 'Maintain Custom Search',
    'version': '13.0.1',
    'category': 'Extra Tools',
    'summary': 'Custom Search Form',
    'depends': ['base', 'web'],
    'data': [
        'views/assets.xml',
    ],
    'author': 'BinhDT',
    'demo': [],
    'qweb': [
            "static/src/xml/Search_Custom_Template.xml",
     ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}