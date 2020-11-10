# -*- coding: utf-8 -*-
{
    'name': "Maintain Master Price List",
    'summary': """Master Price List""",
    'description': """""",

    'author': "SKcompany",
    'website': "https://www.skcompany.net",
    'category': 'Test',
    'version': '0.1',
    'depends': [
        'base_setup',
        'Maintain_Invoice_Remake'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/master_price_list.xml',
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
