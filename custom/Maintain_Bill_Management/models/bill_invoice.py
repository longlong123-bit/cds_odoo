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
    deadline = fields.Date(string='Deadline')
    customer_code = fields.Char(string='Customer Code')
    customer_name = fields.Char(string='Customer Name')
    amount_untaxed = fields.Monetary(string='Amount Untaxed', currency_id='currency_id')
    amount_tax = fields.Monetary(string='Amount Tax', currency_field='currency_id')
    amount_total = fields.Monetary(string='Amount Total', currency_field='currency_id')
    customer_trans_classification_code = fields.Selection([('sale', 'Sale'), ('cash', 'Cash')],
                                                          string='Transaction classification', default='sale')
    currency_id = fields.Many2one('res.currency', string='Currency')
    active_flag = fields.Boolean(default=True)
    hr_employee_id = fields.Many2one('hr.employee', string='Customer Agent')
    hr_department_id = fields.Many2one('hr.department', string='Department')
    business_partner_group_custom_id = fields.Many2one('business.partner.group.custom', string='Supplier Group')
    customer_closing_date_id = fields.Many2one('closing.date', string='Customer Closing Date')
    x_voucher_tax_transfer = fields.Char('x_voucher_tax_transfer')
    invoice_date = fields.Date(string="Invoice Date")
    invoice_no = fields.Char(string='Invoice No')
    x_studio_summary = fields.Text('Summary')
