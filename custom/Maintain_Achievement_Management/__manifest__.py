# -*- coding: utf-8 -*-
{
    'name': 'Maintain Achievement Management',
    'version': '13.0',
    'author': 'Trong Huy',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Invoice_Remake'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/sales_achievement_employee_view.xml',
        'views/sales_achievement_customer_view.xml',
        'views/sales_achievement_customer_employee_view.xml',
        'views/sales_achievement_business_view.xml',
        'views/sales_achievement_customer_business_view.xml',
        'reports/report_format.xml',
        'reports/sales_achievement_employee_report.xml',
        'reports/sales_achievement_customer_report.xml',
        'reports/sales_achievement_customer_employee_report.xml',
        'reports/sales_achievement_business_report.xml',
        'reports/sales_achievement_customer_business_report.xml'
    ],
    'qweb': [
        'static/src/xml/sales_achievement_employee_advanced_search.xml',
        'static/src/xml/sales_achievement_customer_advanced_search.xml',
        'static/src/xml/sales_achievement_customer_business_advanced_search.xml',
        'static/src/xml/sales_achievement_business_advanced_search.xml',
        'static/src/xml/sales_achievement_customer_employee_advanced_search.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

