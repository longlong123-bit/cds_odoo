# -*- coding: utf-8 -*-
{
    'name': 'Business Partner Customer Remake',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup',
        'Maintain_Discount_Schema',
        'Maintain_Bill_Schema',
        'account',
        'Maintain_Business_Partner_Group',
        'Maintain_Closing_Date',
        'Maintain_Payment_Date',
        'Maintain_Custom_Company_Office',
        'Maintain_Custom_Employee',
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/partner_custom_view.xml',
        'views/partner_custom_ref_view.xml',
        'views/sequence.xml',
    ],
    'qweb': [
        'static/src/xml/advanced_search.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': True
}

