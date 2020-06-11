from odoo import models, fields, api


class BillInfoClass(models.Model):
    _name = 'bill.info'

    partner_id = fields.Many2one('res.partner')

    billing_code = fields.Char(string='Billing Code')
    billing_name = fields.Char(string='Billing Name')
    bill_no = fields.Char(string='Bill No')
    bill_date = fields.Date(string='Bill Date')
    last_closing_date = fields.Date(string='Last Closing Date')
    closing_date = fields.Date(string='Closing Date')
    invoices_number = fields.Integer(string='Number of Invoices', default=0)
    invoices_details_number = fields.Integer(string='Number of Invoice Details', default=0)
    last_billed_amount = fields.Monetary(string='Last Billed Amount', currency_field='currency_id')
    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id')
    balance_amount = fields.Monetary(string='Balance Amount', currency_field='currency_id')
    amount_untaxed = fields.Monetary(string='Amount Untaxed', currency_field='currency_id')
    tax_amount = fields.Monetary(string='Tax Amount', currency_field='currency_id')
    amount_total = fields.Monetary(string="Amount Total", currency_field='currency_id')
    amount_untaxed_cashed = fields.Monetary(string='Amount Untaxed Cashed', currency_field='currency_id')
    tax_amount_cashed = fields.Monetary(string='Tax Amount Cashed', currency_field='currency_id')
    amount_total_cashed = fields.Monetary(string="Amount Total Cashed", currency_field='currency_id')
    billed_amount = fields.Monetary(string='Billed Amount', currency_field='currency_id')
    active_flag = fields.Boolean(default=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    bill_invoice_ids = fields.One2many('bill.invoice', 'bill_info_id', string='Bill Invoice Ids')
    report_status = fields.Char(string='Report Status', default='no report')

    _sql_constraints = [('bill_info', 'unique(billing_code, last_closing_date)', 'Bill must be unique!')]
