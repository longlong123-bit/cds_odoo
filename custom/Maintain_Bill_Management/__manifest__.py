# -*- coding: utf-8 -*-
{
    'name': "Bill Management",
    'summary': """Manage bill""",
    'description': """""",

    'author': "SKcompany",
    'website': "https://www.skcompany.net",

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base_setup', 'Maintain_Custom_Department', 'Maintain_Custom_Department_Section',
        'Maintain_Custom_Employee', 'Maintain_Business_Partner_Group', 'Maintain_Closing_Date',
        'Maintain_Product_Class', 'Maintain_Product', 'Maintain_Freight_Category',
        'Maintain_Business_Partners_Remake', 'Maintain_Invoice_Remake', 'Maintain_Accounts_Receivable_Balance_List',
        'Maintain_Income_Payment'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/bill.xml',
        'views/bill_details.xml',
        'views/menu_bill_management.xml',
        'views/many_payment_view.xml',
    ],
    'qweb': [
        'static/src/xml/bill_advanced_search.xml',
        'static/src/xml/bill_product_lines.xml',
        'static/src/xml/create_bill_button.xml',
    ],

    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
