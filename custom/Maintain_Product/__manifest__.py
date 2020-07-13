# -*- coding: utf-8 -*-
{
    'name': 'Product Custom',
    'version': '13.0',
    'author': 'BinhDT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'sale_management', 'Maintain_Organization', 'Maintain_Client', 'Maintain_Product_Class'
    ],
    'website': '',
    'depends':['product', 'purchase', 'sale'],
    'data': [
        'data/tax_tax_data.xml',

        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/product_custom_view.xml',
        'views/product_confirm_view.xml',
        'views/tax_tax_view.xml',
    ],
    'qweb': [
        'static/src/xml/advanced_search.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

