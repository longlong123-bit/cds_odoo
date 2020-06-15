from odoo import models, fields, api


class BillInvoiceDetailsClass(models.Model):
    _name = 'bill.invoice.details'

    bill_info_id = fields.Many2one('bill_info')
    bill_invoice_id = fields.Many2one('bill_invoice')
    account_move_line_id = fields.Many2one('account.move.line')
    account_move_line_id = fields.Many2one('account.move.line')

    billing_code = fields.Char(string='Billing Code')
    billing_name = fields.Char(string='Billing Name')
    bill_no = fields.Char(string='Bill No')
    bill_date = fields.Date(string="Bill Date")
    last_closing_date = fields.Date(string='Last Closing Date')
    closing_date = fields.Date(string='Closing Date')
    customer_code = fields.Char(string='Customer Code')
    customer_name = fields.Char(string='Customer Name')
    customer_trans_classification_code = fields.Selection([('sale', 'Sale'), ('cash', 'Cash')],
                                                          string='Transaction classification', default='sale')
    active_flag = fields.Boolean(default=True)
    hr_employee_id = fields.Many2one('hr.employee', string='Customer Agent')
    hr_department_id = fields.Many2one('hr.department', string='Department')
    business_partner_group_custom_id = fields.Many2one('business.partner.group.custom', string='Supplier Group')
    customer_closing_date_id = fields.Many2one('closing.date', string='Customer Closing Date')