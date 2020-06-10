from odoo import models, fields, api


class BillInvoiceClass(models.Model):
    _name = 'bill.invoice'

    bill_info_id = fields.Many2one('bill.info', string='Bill Info')
    bill_invoice_details_ids = fields.One2many('bill.invoice.details', 'bill_invoice_id', string='Bill Invoice Details')
    account_move_id = fields.Many2one('account.move')

    billing_code = fields.Char(string='Billing Code')
    billing_name = fields.Char(string='Billing Name')
    bill_no = fields.Char(string='Bill No')
    bill_date = fields.Date(string='Bill Date')
    last_closing_date = fields.Date(string='Last Closing Date')
    closing_date = fields.Date(string='Closing Date')
    amount_untaxed = fields.Monetary(string='Amount Untaxed', currency_id='currency_id')
    amount_tax = fields.Monetary(string='Amount Tax', currency_field='currency_id')
    amount_total = fields.Monetary(string='Amount Total', currency_field='currency_id')
    customer_trans_classification_code = fields.Selection([('sale', 'Sale'), ('cash', 'Cash')],
                                                          string='Transaction classification', default='sale')
    currency_id = fields.Many2one('res.currency', string='Currency')
    active_flag = fields.Boolean(default=True)
