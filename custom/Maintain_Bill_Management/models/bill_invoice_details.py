from odoo import models, fields, api


class BillInvoiceDetailsClass(models.Model):
    _name = 'bill.invoice.details'

    bill_invoice_id = fields.Many2one('bill_invoice')
    account_move_line_id = fields.Many2one('account.move.line')
    account_move_line_id = fields.Many2one('account.move.line')

    billing_code = fields.Char(string='Billing Code')
    billing_name = fields.Char(string='Billing Name')
    bill_no = fields.Char(string='Bill No')
    bill_date = fields.Date(string="Bill Date")
    last_closing_date = fields.Date(string='Last Closing Date')
    closing_date = fields.Date(string='Closing Date')
    customer_trans_classification_code = fields.Selection([('sale', 'Sale'), ('cash', 'Cash')],
                                                          string='Transaction classification', default='sale')
    active_flag = fields.Boolean(default=True)
