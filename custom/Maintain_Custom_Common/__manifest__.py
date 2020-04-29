# -*- coding: utf-8 -*-
{
    'name': 'Maintain Custom Common',
    'version': '13.0.1',
    'category': 'Extra Tools',
    'summary': 'Custom Common: Pager,Css,List,Form,..',
    'depends': ['base', 'web'],
    'data': [
        'views/assets.xml',
    ],
    'author': 'BinhDT',
    'demo': [],
    'qweb': [
            "static/src/xml/pager_template.xml",
             "static/src/xml/notice_template.xml",
     ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}