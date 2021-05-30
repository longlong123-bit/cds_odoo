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
    deadline = fields.Date(string='Deadline')
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
    payment_discount_in_invoicing = fields.Monetary(currency_field='currency_id')
    active_flag = fields.Boolean(default=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    bill_invoice_ids = fields.One2many('bill.invoice', 'bill_info_id', string='Bill Invoice Ids')
    # report_status = fields.Char(string='Report Status', default='no report')
    hr_employee_id = fields.Many2one('hr.employee', string='Customer Agent')
    hr_department_id = fields.Many2one('hr.department', string='Department')
    business_partner_group_custom_id = fields.Many2one('business.partner.group.custom', string='Supplier Group')
    customer_closing_date_id = fields.Many2one('closing.date', string='Customer Closing Date')
    customer_excerpt_request = fields.Boolean(string='Excerpt Request', default=False)
    bill_report_state = fields.Boolean(string="Bill Report State", default=False)
    payment_cost_and_discount = fields.Float(string='Payment Cost And Discount')
    payment_plan_date = fields.Char(string='Payment Plan Date', store=True)

    _sql_constraints = [
        ('bill_info', 'unique(billing_code, last_closing_date, deadline)', 'This data has been billed.')]

    last_billed_amount_int_format = fields.Integer(string='Last Billed Amount', compute='_last_billed_amount_int_format'
                                                   , readonly=True)
    deposit_amount_int_format = fields.Integer(string='Deposit Amount', compute='_deposit_amount_int_format'
                                               , readonly=True)
    balance_amount_int_format = fields.Integer(string='Balance Amount', compute='_balance_amount_int_format'
                                               , readonly=True)

    amount_untaxed_int_format = fields.Integer(string='Amount Untaxed', compute='_amount_untaxed_int_format'
                                               , readonly=True)

    tax_amount_int_format = fields.Integer(string='Tax Amount', compute='_tax_amount_int_format', readonly=True)

    amount_total_int_format = fields.Integer(string="Amount Total", compute='_amount_total_int_format', readonly=True)

    billed_amount_int_format = fields.Integer(string='Billed Amount', compute='_billed_amount_int_format'
                                              , readonly=True)

    def _last_billed_amount_int_format(self):
        for rec in self:
            rec.last_billed_amount_int_format = int(rec.last_billed_amount)

    def _deposit_amount_int_format(self):
        for rec in self:
            rec.deposit_amount_int_format = int(rec.deposit_amount)

    def _balance_amount_int_format(self):
        for rec in self:
            rec.balance_amount_int_format = int(rec.balance_amount)

    def _amount_untaxed_int_format(self):
        for rec in self:
            rec.amount_untaxed_int_format = int(rec.amount_untaxed)

    def _tax_amount_int_format(self):
        for rec in self:
            rec.tax_amount_int_format = int(rec.tax_amount)

    def _amount_total_int_format(self):
        for rec in self:
            rec.amount_total_int_format = int(rec.amount_total)

    def _billed_amount_int_format(self):
        for rec in self:
            rec.billed_amount_int_format = int(rec.billed_amount)


# class ResPartnerIntFormat(models.Model):
#     _name = 'res.partner'
#     _inherit = 'res.partner'
#
#     last_billed_amount_int_format = fields.Integer(string='Last Billed Amount', compute='_last_billed_amount_int_format'
#                                                    , readonly=True)
#     deposit_amount_int_format = fields.Integer(string='Deposit Amount', compute='_deposit_amount_int_format'
#                                                , readonly=True)
#     balance_amount_int_format = fields.Integer(string='Balance Amount', compute='_balance_amount_int_format'
#                                                , readonly=True)
#
#     amount_untaxed_int_format = fields.Integer(string='Amount Untaxed', compute='_amount_untaxed_int_format'
#                                                , readonly=True)
#
#     tax_amount_int_format = fields.Integer(string='Tax Amount', compute='_tax_amount_int_format', readonly=True)
#
#     amount_total_int_format = fields.Integer(string="Amount Total", compute='_amount_total_int_format', readonly=True)
#
#     billed_amount_int_format = fields.Integer(string='Billed Amount', compute='_billed_amount_int_format'
#                                               , readonly=True)
#
#     def _last_billed_amount_int_format(self):
#         for rec in self:
#             rec.last_billed_amount_int_format = int(rec.last_billed_amount)
#
#     def _deposit_amount_int_format(self):
#         for rec in self:
#             rec.deposit_amount_int_format = int(rec.deposit_amount)
#
#     def _balance_amount_int_format(self):
#         for rec in self:
#             rec.balance_amount_int_format = int(rec.balance_amount)
#
#     def _amount_untaxed_int_format(self):
#         for rec in self:
#             rec.amount_untaxed_int_format = int(rec.amount_untaxed)
#
#     def _tax_amount_int_format(self):
#         for rec in self:
#             rec.tax_amount_int_format = int(rec.tax_amount)
#
#     def _amount_total_int_format(self):
#         for rec in self:
#             rec.amount_total_int_format = int(rec.amount_total)
#
#     def _billed_amount_int_format(self):
#         for rec in self:
#             rec.billed_amount_int_format = int(rec.billed_amount)

