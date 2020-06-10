# -*- coding: utf-8 -*-
{
    'name': 'Accounts Receivable Balance List',
    'version': '13.0',
    'author': 'NghiaNT',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup','account', 'Maintain_Client', 'Maintain_Organization','inputmask_widget','Maintain_Bill_Schema','Maintain_Business_Partner_Group','Maintain_Business_Partners_Remake',
        'Maintain_Closing_Date','Maintain_Country_State','Maintain_Custom_Common','Maintain_Custom_Company_Office','Maintain_Custom_Create_Company','Maintain_Custom_Department',
        'Maintain_Custom_Department_Section','Maintain_Custom_Employee','Maintain_Custom_Search_Form','Maintain_Discount_Schema','Maintain_Freight_Category',
        'Maintain_Income_Payment','Maintain_Industry_Type','Maintain_Invoice_Print','Maintain_Organization','Maintain_Printer_Output',
        'Maintain_Product','Maintain_Product_Class','Maintain_Quotations','Maintain_Receipt_Divide','Maintain_Tax_Rate','Maintain_Widget_Sale_History','tgl_format_number'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/add_js.xml',
        'views/accounts_receivable_balance_list_view.xml',
        'report/report_accounts_receivable_balance_list.xml',
        'report/report.xml'
    ],
    'qweb': [
        'static/src/xml/advanced_search.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}

