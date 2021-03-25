from odoo import models, fields, api
from datetime import date
from ...Maintain_Invoice_Remake.models.invoice_customer_custom import rounding
from ...Maintain_Accounts_Receivable_Balance_List.models import accounts_receivable_balance_list as advanced_search


class BillingDetailsClass(models.TransientModel):
    _name = 'bill.details'
    _rec_name = 'billing_code'

    @api.depends('deadline', 'last_closing_date')
    def prepare_data_for_bill_details_line(self):
        ctx = self._context.copy()
        domain = [
            ('x_studio_date_invoiced', '<=', self.deadline),
            ('state', '=', 'posted'),
            ('bill_status', '!=', 'billed'),
            '|', ('partner_id.customer_code_bill', '=', self.billing_code),
            ('partner_id.customer_code', '=', self.billing_code),
        ]
        if ctx.get('last_closing_date'):
            domain += [('x_studio_date_invoiced', '>', self.last_closing_date)]
        bill_account_move_ids = self.env['account.move'].search(domain)
        invoice_line_domain = [
            ('move_id', 'in', bill_account_move_ids.ids),
            ('date', '<=', self.deadline),
            ('bill_status', '=', 'not yet'),
            ('parent_state', '=', 'posted'),
            ('price_total', '!=', 0),
            ('account_internal_type', '=', 'other'),
        ]

        if ctx.get('last_closing_date'):
            invoice_line_domain += [('date', '>', self.last_closing_date)]
        invoice_line_ids = self.env['account.move.line'].search(invoice_line_domain)
        vals = []
        for invoice_line in invoice_line_ids:
            # calculate untaxed amount
            _line_untaxed_amount = invoice_line.invoice_custom_lineamount

            # calculate tax
            if invoice_line.move_id.x_voucher_tax_transfer == 'foreign_tax' \
                    or invoice_line.move_id.x_voucher_tax_transfer == 'internal_tax':
                _line_tax_amount = rounding(invoice_line.line_tax_amount, 0, invoice_line.move_id.customer_tax_rounding)
            elif invoice_line.move_id.x_voucher_tax_transfer == 'voucher':
                _line_tax_amount = invoice_line.voucher_line_tax_amount
            elif invoice_line.move_id.x_voucher_tax_transfer == 'invoice':
                _line_tax_amount = rounding(invoice_line.invoice_custom_lineamount * invoice_line.tax_rate / 100,
                                            2,
                                            invoice_line.move_id.customer_tax_rounding)
            elif invoice_line.move_id.x_voucher_tax_transfer == 'custom_tax':
                _line_tax_amount = 0

            # calculate line amount
            _line_amount = _line_untaxed_amount + _line_tax_amount

            vals += [{
                'selected': invoice_line.selected,
                'invoice_date': invoice_line.date,
                'invoice_no': invoice_line.invoice_no,
                'customer_code': invoice_line.customer_code,
                'customer_name': invoice_line.customer_name,
                'invoice_line_type': invoice_line.x_invoicelinetype,
                'product_code': invoice_line.product_code,
                'product_name': invoice_line.product_name,
                'product_maker_name': invoice_line.product_maker_name,
                'product_standard_number': invoice_line.invoice_custom_standardnumber,
                'quantity': invoice_line.quantity,
                'price_unit': invoice_line.price_unit,
                'untaxed_amount': _line_untaxed_amount,
                'tax_amount': _line_tax_amount,
                'line_amount': _line_amount,
                'note': invoice_line.invoice_custom_Description,

                # Invisible Fields
                'account_move_id': invoice_line.move_id.id,
                'account_move_line_id': invoice_line.id,
                'billing_place_id': self.billing_place_id.id,
                'partner_id': invoice_line.partner_id.id,
            }]
        lines = self.env['bill.details.line'].create(vals)
        self.bill_details_line_ids = [(6, 0, lines.ids)]

    billing_place_id = fields.Many2one('res.partner', readonly=True)
    billing_code = fields.Char(string='Billing Code', readonly=True)
    billing_name = fields.Char(string='Billing Name', readonly=True)
    deadline = fields.Date(string='Deadline', readonly=True)
    last_closing_date = fields.Date(string='Last Closing Date', readonly=True)
    last_billed_amount = fields.Float(string='Last Billed Amount', readonly=True)

    bill_details_line_ids = fields.One2many('bill.details.line', 'bill_details_id', string='Bill Details Line',
                                            compute='prepare_data_for_bill_details_line', store=True)

    def create_bill_details(self):
        invoiced_ids = []
        for line in self.bill_details_line_ids:
            invoice = line.account_move_id
            if line.selected:
                if invoice and invoice.id not in invoiced_ids:
                    invoiced_ids.append(invoice.id)
                    invoice.write({
                        'selected': True
                    })

                line.account_move_line_id.write({
                    'selected': True
                })
            else:
                line.account_move_line_id.write({
                    'selected': False
                })
        invoice_unselected = self.bill_details_line_ids.mapped('account_move_line_id.move_id').filtered(
            lambda l: l.id not in invoiced_ids)
        invoice_unselected.write({
            'selected': False
        })

        # for ids in all_invoiced_ids
        self.prepare_data_for_bill_details_line()

        advanced_search.val_bill_search_deadline = ''
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
    _order = 'invoice_date asc, invoice_no asc, customer_code asc'

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

    # Invisible fields
    account_move_id = fields.Many2one('account.move', 'Account Move Id')
    account_move_line_id = fields.Many2one('account.move.line', 'Account Move Line Id')
    billing_place_id = fields.Many2one('res.partner', 'Billing Place Id')
    partner_id = fields.Many2one('res.partner', 'Partner Id')
    payment_id = fields.Many2one('account.payment', 'Payment Id')
