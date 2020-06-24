# -*- coding: utf-8 -*-
{
    'name': 'Normal Reports',
    'version': '13.0',
    'author': 'TaiBX',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'sale_management', 'Maintain_Organization', 'Maintain_Client'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/menu.xml',
        'reports/normal_reports_2_in_1.xml',
        'reports/normal_reports_1_in_1.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
