# -*- coding: utf-8 -*-
{
    'name': 'Leads Custom',
    'version': '13.0',
    'author': 'Longdn',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup',
        'crm',
        'utm'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_custom_views.xml',
        'views/menu_crm.xml',
        'views/utm_campaign_views.xml',
        'views/crm_templates.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

