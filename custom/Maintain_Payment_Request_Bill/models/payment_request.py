from odoo import api, fields, models
# from datetime import date


class PrintPaymentRequest(models.Model):
    _inherit = 'bill.invoice'

    # def _get_value_1(self):
    #     for con in self:
    #         con.bill_info_id = self.env['bill.info'].search([('billing_code', '=', con.billing_code)]).id
    # con.billing_code1 = con.bill_info_id.billing_code
    # con.billing_name1 = con.bill_info_id.billing_name
    # con.bill_no1 = con.bill_info_id.
    # con.amount_total1 = con.bill_info_id.amount_total
    # @api.onchange('bill_info_id')
    # def _get_bill_info_id(self):
    #     for bill in self:
    #         bill.bill_info_id = self.env['bill.info'].search([('last_closing_date', '=', bill.last_closing_date),
    #                                                           ('billing_code', '=', bill.billing_code)]).id
    #         print(bill.bill_info_id)
    #     print('Run')

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


    # Custom preview invoice
    # def preview_invoice(self):
    #     return {
    #         'type': 'ir.actions.report',
    #         'report_name': 'Maintain_Payment_Request_Bill.payment_request_bill',
    #         'model': 'bill.invoice',
    #         'report_type': "qweb-html",
    #     }
    # @api.one


class BillInfoGet(models.Model):
    _inherit = 'bill.info'

    def _get_customer_other_cd(self):
        for cd in self:
            # if self.partner_id:
            cd.customer_other_cd = cd.partner_id.customer_other_cd
        # self.bill_report_print_date = date.today()
        # print(self.bill_report_print_date)

    # その他CD
    customer_other_cd = fields.Char('Customer CD', readonly=True, compute='_get_customer_other_cd')
    # bill_report_print_date = fields.Date('bill_report_print_date', compute='_get_customer_other_cd', store=False)


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
