from odoo import api, fields, models


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

    # billing_code1 = fields.Char('billing_code')
    # billing_name1 = fields.Char('billing_name')
    # bill_no1 = fields.Char('bill_no')
    # last_billed_amount1 = fields.Char('last_billed_amount')
    # deposit_amount1 = fields.Char('deposit_amount')
    # balance_amount1 = fields.Char('balance_amount')
    # amount_untaxed1 = fields.Char('amount_untaxed')
    # tax_amount1 = fields.Char('tax_amount')
    # amount_total1 = fields.Char('amount_total', compute='_get_value_1', store=False)
    # last_closing_date1 = fields('last_closing_date')
    # customer_other_cd1 = fields.Char('customer_other_cd')
    # invoices_number1 = fields.Char('invoices_number')

    # bill_invoice_ids = fields.One2many('bill.invoice', 'bill_info_id', string='Bill Invoice Ids')
    # def _get_bill_invoice_ids(self):
    #     for ge in self:
    #         print(ge.billing_code)
    #         print(ge.last_closing_date)
    #         ge.bill_invoice_ids = self.env['bill.invoice'].search(
    #             [('billing_code', '=', ge.billing_code), ('last_closing_date', '=', ge.last_closing_date)])
    #         print(ge.bill_invoice_ids)
    # def report_dialog(self):
    #     return {
    #         'type': ''
    #     }

    # Custom preview invoice
    def preview_invoice(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Maintain_Payment_Request_Bill.payment_request_bill',
            'model': 'bill.invoice',
            'report_type': "qweb-html",
        }
    # @api.one


class BillInfoGet(models.Model):
    _inherit = 'bill.info'

    def _get_customer_other_cd(self):
        for cd in self:
            # if self.partner_id:
            cd.customer_other_cd = cd.partner_id.customer_other_cd

    # その他CD
    customer_other_cd = fields.Char('Customer CD', readonly=True, compute='_get_customer_other_cd')
