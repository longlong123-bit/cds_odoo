from odoo import api, fields, models
# from datetime import date
from datetime import date, timedelta


class PrintPaymentRequest(models.Model):
    _inherit = 'bill.invoice'

    last_billed_amount = fields.Monetary(string='Last Billed Amount', currency_field='currency_id')
    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id')
    balance_amount = fields.Monetary(string='Balance Amount', currency_field='currency_id')
    tax_amount = fields.Monetary(string='Tax Amount', currency_field='currency_id')
    customer_other_cd = fields.Char('Customer CD', readonly=True)
    invoices_number = fields.Integer(string='Number of Invoices', default=0)
    # con.

    bill_user_id = fields.Many2one('res.users', copy=False, tracking=True,
                                   string='Salesperson',
                                   default=lambda self: self.env.user)


class BillInfoGet(models.Model):
    _inherit = 'bill.info'

    def _get_customer_other_cd(self):
        for cd in self:
            # if self.partner_id:
            cd.customer_other_cd = cd.partner_id.customer_other_cd

    # その他CD
    customer_other_cd = fields.Char('Customer CD', readonly=True, compute='_get_customer_other_cd')


class PartnerClass(models.Model):
    _inherit = 'res.partner'

    def set_supplier_name(self):
        for i in self:
            if i.group_supplier:
                i.group_supplier = i.customer_supplier_group_code.name

    group_supplier = fields.Char('set_supplier_name', compute='set_supplier_name')


class InvoiceClassCustom(models.Model):
    _inherit = 'account.move'

    # account_invoice_id
    payment_id = fields.One2many('account.payment', 'account_invoice_id')
    bill_invoice_ids = fields.One2many('bill.invoice', 'account_move_id')
