# -*- coding: utf-8 -*-
{
    'name': "Bill Management",
    'summary': """Manage bill""",
    'description': """
        Open Academy module for managing trainings:
            - training courses
            - training sessions
            - attendees registration
    """,

    'author': "SKcompany",
    'website': "https://www.skcompany.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 'base_setup', 'Maintain_Client',
        'Maintain_Business_Partners_Remake', 'Maintain_Invoice_Remake'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/bill.xml',
        'views/menu_bill_management.xml',
        'views/cancel_bill.xml',
    ],
    'qweb': [
        'static/src/xml/bill_advanced_search.xml',
        'static/src/xml/bill_product_lines.xml',
        'static/src/xml/create_bill_button.xml',
        'static/src/xml/cancel_bill_button.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
