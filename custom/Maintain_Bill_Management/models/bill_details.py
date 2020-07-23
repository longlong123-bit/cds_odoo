from odoo import models, fields, api
from datetime import datetime, date, timedelta


class BillingDetailsClass(models.TransientModel):
    _name = 'bill.details'
    _rec_name = 'billing_code'

    @api.depends('deadline', 'last_closing_date')
    def prepare_data_for_bill_details_line(self):
        ctx = self._context.copy()
        domain = [
            ('partner_id.customer_code_bill', '=', self.billing_code),
            ('x_studio_date_invoiced', '<=', self.deadline),
            ('state', '=', 'posted'),
            ('bill_status', '!=', 'billed')
        ]
        if ctx.get('last_closing_date'):
            domain += [('x_studio_date_invoiced', '>', self.last_closing_date)]
        bill_account_move_ids = self.env['account.move'].search(domain)

        invoice_line_domain = [
            ('move_id', 'in', bill_account_move_ids.ids),
            ('date', '<=', self.deadline),
            ('bill_status', '=', 'not yet'),
            ('parent_state', '=', 'posted'),
            ('credit', '!=', 0),
            ('account_internal_type', '=', 'other'),
        ]

        payment_line_domain = [
            ('partner_id.customer_code_bill', '=', self.billing_code),
            ('payment_date', '<=', self.deadline),
            ('state', '=', 'draft'),
            ('bill_status', '!=', 'billed'),
        ]

        if ctx.get('last_closing_date'):
            invoice_line_domain += [('date', '>', self.last_closing_date)]
            payment_line_domain += [('payment_date', '>', self.last_closing_date)]
        invoice_line_ids = self.env['account.move.line'].search(invoice_line_domain)
        payment_ids = self.env['account.payment'].search(payment_line_domain)
        vals = []
        for invoice in invoice_line_ids:
            vals += [{
                'invoice_date': invoice.date,
                'invoice_no': invoice.invoice_no,
                'customer_code': invoice.customer_code,
                'customer_name': invoice.customer_name,
                'invoice_line_type': invoice.x_invoicelinetype,
                'product_code': invoice.product_code,
                'product_name': invoice.product_name,
                'product_maker_name': invoice.product_maker_name,
                'product_standard_number': invoice.invoice_custom_standardnumber,
                'quantity': invoice.quantity,
                'price_unit': invoice.price_unit,
                'untaxed_amount': invoice.invoice_custom_lineamount,
                'tax_amount': invoice.invoice_custom_lineamount,
                'line_amount': invoice.invoice_custom_lineamount,
                'note': invoice.invoice_custom_Description,
            }]
        for payment in payment_ids:
            vals += [{
                'invoice_date': payment.payment_date,
                'invoice_no': payment.document_no,
                'customer_code': payment.partner_id.customer_code,
                'customer_name': payment.partner_id.name,
                'invoice_line_type': '',
                'product_code': '',
                'product_name': '',
                'product_maker_name': '',
                'product_standard_number': '',
                'quantity': 1,
                'price_unit': False,
                'untaxed_amount': False,
                'tax_amount': False,
                'line_amount': payment.amount * -1,
                'note': payment.description,
            }]
        lines = self.env['bill.details.line'].create(vals)
        self.bill_details_line_ids = [(6, 0, lines.ids)]

    billing_code = fields.Char(string='Billing Code', readonly=True,)
    billing_name = fields.Char(string='Billing Name', readonly=True,)
    deadline = fields.Date(string='Deadline', readonly=True,)
    last_closing_date = fields.Date(string='Last Closing Date', readonly=True,)

    bill_details_line_ids = fields.One2many('bill.details.line', 'bill_details_id', string='Bill Details Line',
                                            compute='prepare_data_for_bill_details_line', store=True)

    def create_bill_details(self):


        return True

    def check_all_button(self):
        self.bill_details_line_ids = [(1, self.bill_details_line_ids.ids, {'selected': True})]
        return True

    def uncheck_all_button(self):
        self.bill_details_line_ids.write({
            'selected': False
        })
        return True


class BillDetailsLineClass(models.TransientModel):
    _name = 'bill.details.line'

    bill_details_id = fields.Many2one('bill.details', 'Bill Details')
    selected = fields.Boolean(default=False)
    invoice_date = fields.Date(string='Invoice Date')
    invoice_no = fields.Char(string='Invoice No')
    customer_code = fields.Char(string='Customer Code')
    customer_name = fields.Char(string='Customer Name')
    invoice_line_type = fields.Char(string='Invoice Line Type')
    product_code = fields.Char(string='Product Code')
    product_name = fields.Char(string='Product Name')
    product_maker_name = fields.Char(string='Product Maker Name')
    product_standard_number = fields.Char(string='Product Standard Number')
    quantity = fields.Integer(string='Quantity')
    price_unit = fields.Float(string='Price Unit')
    untaxed_amount = fields.Float(string='Untaxed Amount')
    tax_amount = fields.Float(string='Tax Amount')
    line_amount = fields.Float(string='Line Amount')
    note = fields.Char(string='Note')
