# -*- coding: utf-8 -*-
{
    'name': "Bill Management - Bill List",
    'summary': """Manage bill""",
    'description': """""",

    'author': "SKcompany",
    'website': "https://www.skcompany.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 'base_setup', 'sale', 'Maintain_Bill_Management',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/list_bill.xml',
        'reports/report.xml',
        'reports/report_template.xml',
    ],
    'qweb': [
        'static/src/xml/bill_list_advanced_search.xml',
    ],

    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'auto_install': False,
}
