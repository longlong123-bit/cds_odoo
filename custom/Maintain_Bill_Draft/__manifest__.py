# -*- coding: utf-8 -*-
{
    'name': "Bill Management - Draft Bill",
    'summary': """Manage bill""",
    'description': """
        Open Academy module for managing trainings:
            - training courses
            - training sessions
            - attendees registration
    """,

    'author': "SKcompany",
    'website': "https://www.skcompany.net",
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_setup',
        'sale',
        'Maintain_Bill_Management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/history_draft_bill.xml',
    ],
    'qweb': [
        'static/src/xml/draft_bill_advanced_search.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
