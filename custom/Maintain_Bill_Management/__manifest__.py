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
        'base_setup',
        'Maintain_Business_Partners_Remake',
        'Maintain_Invoice_Remake',
        'Maintain_Income_Payment',
        'Maintain_Accounts_Receivable_Balance_List',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/bill.xml',
        'views/draft_bill.xml',
        'views/menu_bill_management.xml',
        'views/many_payment_view.xml',
        'views/bill_details.xml',
        'views/report.xml',
        'reports/reports.xml',
        'reports/normal_reports_draft.xml',
        'reports/abstract_payment_reports_draft.xml',
        'reports/current_month_reports_draft.xml',
        'reports/deposit_reports_draft.xml',
        'reports/deposit_reports_draft_1.xml',
        'reports/normal_invoice_for_earch_customer_report_draft.xml',
        'reports/yamasa_invoice_reports_draft.xml',
        'reports/deposit_reports_draft.xml'
    ],
    'qweb': [
        'static/src/xml/bill_advanced_search.xml',
        'static/src/xml/bill_product_lines.xml',
        'static/src/xml/create_bill_button.xml',
        'static/src/xml/create_review_button.xml',
    ],

    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
