# -*- coding: utf-8 -*-
{
    'name': 'Country State',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup',  'Maintain_Client', 'Maintain_Industry_Type', 'Maintain_Custom_Department', 'Maintain_Custom_Department_Section', 'Maintain_Custom_Employee',
        'Maintain_Closing_Date', 'Maintain_Tax_Rate', 'Maintain_Printer_Output', 'Maintain_Custom_Create_Company', 'Maintain_Business_Partner_Group', 'Maintain_Product_Class'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/custom_country_state_view.xml',
        'views/menu_new_master.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

