from odoo import models, fields, api


class BillInvoiceDetailsClass(models.Model):
    _name = 'bill.invoice.details'

    bill_info_id = fields.Many2one('bill.info')
    bill_invoice_id = fields.Many2one('bill.invoice')
    account_move_line_id = fields.Many2one('account.move.line')
    payment_id = fields.Many2one('account.payment')

    billing_code = fields.Char(string='Billing Code')
    billing_name = fields.Char(string='Billing Name')
    bill_no = fields.Char(string='Bill No')
    bill_date = fields.Date(string="Bill Date")
    last_closing_date = fields.Date(string='Last Closing Date')
    closing_date = fields.Date(string='Closing Date')
    deadline = fields.Date(string='Deadline')
    customer_code = fields.Char(string='Customer Code')
    customer_name = fields.Char(string='Customer Name')
    customer_trans_classification_code = fields.Selection([('sale', 'Sale'), ('cash', 'Cash')],
                                                          string='Transaction classification', default='sale')
    active_flag = fields.Boolean(default=True)
    hr_employee_id = fields.Many2one('hr.employee', string='Customer Agent')
    hr_department_id = fields.Many2one('hr.department', string='Department')
    business_partner_group_custom_id = fields.Many2one('business.partner.group.custom', string='Supplier Group')
    customer_closing_date_id = fields.Many2one('closing.date', string='Customer Closing Date')
    x_voucher_tax_transfer = fields.Char('x_voucher_tax_transfer')
    invoice_date = fields.Date(string="Invoice Date")
    invoice_no = fields.Char(string='Invoice No')
    quantity = fields.Float('Quantity', readonly=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    tax_amount = fields.Float('tax_amount', readonly=True)
    line_amount = fields.Float('line amount', readonly=True)
    tax_rate = fields.Float('tax_rate', readonly=True)
    voucher_line_tax_amount = fields.Float('Voucher Line Tax Amount', readonly=True)
    payment_category = fields.Selection([('cash', '現金'), ('bank', '銀行')], readonly=True)
