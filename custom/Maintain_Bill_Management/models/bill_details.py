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
                'payment_id': None,

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
                'quantity': None,
                'price_unit': None,
                'untaxed_amount': None,
                'tax_amount': None,
                'line_amount': payment.amount * -1,
                'note': payment.description,

                # Invisible Fields
                'account_move_id': None,
                'account_move_line_id': None,
                'billing_place_id': self.billing_place_id.id,
                'partner_id': payment.partner_id.id,
                'payment_id': payment.id,
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
        if len(self.bill_details_line_ids.filtered(lambda l: l.selected)):
            # Local Variable
            _bill_no = self.env['ir.sequence'].next_by_code('bill.sequence')
            _invoices_number = len(
                self.bill_details_line_ids.filtered(lambda l: l.selected).mapped('account_move_line_id.move_id')) + len(
                self.bill_details_line_ids.filtered(lambda l: l.selected).mapped('payment_id.id'))
            _deposit_amount = 0
            _balance_amount = 0
            _amount_untaxed = 0
            _tax_amount = 0
            _amount_total = 0
            _amount_untaxed_cashed = 0
            _tax_amount_cashed = 0
            _amount_total_cashed = 0

            # Do calculate amount
            for line in self.bill_details_line_ids.filtered(lambda l: l.selected):
                if line.payment_id:
                    _deposit_amount += line.line_amount
                else:
                    _amount_untaxed += line.untaxed_amount
                    _tax_amount += line.tax_amount
                    _amount_total += line.line_amount
                    if line.account_move_id.customer_trans_classification_code == 'cash':
                        _amount_untaxed_cashed += line.untaxed_amount
                        _tax_amount_cashed += line.tax_amount
                        _amount_total_cashed += line.line_amount

            _invoice_custom_tax = self.bill_details_line_ids.filtered(
                lambda l: l.account_move_id.x_voucher_tax_transfer == 'custom_tax').mapped(
                'account_move_line_id.move_id')

            for invoice in _invoice_custom_tax:
                _selected_bill_details_line_custom_tax = self.bill_details_line_ids.filtered(
                    lambda l: (l.selected and l.account_move_id.id == invoice.id))
                _all_bill_details_line_custom_tax = self.bill_details_line_ids.filtered(
                    lambda l: (l.account_move_id.id == invoice.id))
                if len(_selected_bill_details_line_custom_tax) == len(_all_bill_details_line_custom_tax):
                    _tax_amount += invoice.amount_tax
                    _amount_total += invoice.amount_tax
                    if invoice.customer_trans_classification_code == 'cash':
                        _tax_amount_cashed += invoice.amount_tax
                        _amount_total_cashed += invoice.amount_tax

            _balance_amount = _deposit_amount + self.last_billed_amount
            _billed_amount = _amount_total + _balance_amount or 0

            # Create data for bill_info table
            _bill_info_ids = self.env['bill.info'].create({
                'billing_code': self.billing_code,
                'billing_name': self.billing_name,
                'bill_no': _bill_no,
                'bill_date': date.today(),
                'last_closing_date': self.last_closing_date,
                'closing_date': self.deadline,
                'deadline': self.deadline,
                'invoices_number': _invoices_number,
                'invoices_details_number': len(self.bill_details_line_ids.filtered(lambda l: l.selected)),
                'last_billed_amount': self.last_billed_amount,
                'deposit_amount': _deposit_amount,
                'balance_amount': _balance_amount,
                'amount_untaxed': _amount_untaxed,
                'tax_amount': _tax_amount,
                'amount_total': _amount_total,
                'amount_untaxed_cashed': _amount_untaxed_cashed,
                'tax_amount_cashed': _tax_amount_cashed,
                'amount_total_cashed': _amount_total_cashed,
                'billed_amount': _billed_amount,
                'partner_id': self.billing_place_id.id,
                'hr_employee_id': self.billing_place_id.customer_agent.id,
                'hr_department_id': self.billing_place_id.customer_agent.department_id.id,
                'business_partner_group_custom_id': self.billing_place_id.customer_supplier_group_code.id,
                'customer_closing_date_id': self.billing_place_id.customer_closing_date.id,
                'customer_excerpt_request': self.billing_place_id.customer_except_request,
            })

            invoiced_ids = []
            for line in self.bill_details_line_ids.filtered(lambda l: l.selected):
                invoice = line.account_move_id
                _bill_invoice_ids = None
                if invoice and invoice.id not in invoiced_ids:
                    invoiced_ids.append(invoice.id)
                    _line_selected_in_invoice = self.bill_details_line_ids.filtered(
                        lambda l: (l.selected and l.account_move_id.id == invoice.id))
                    _all_line_selected_in_invoice = self.bill_details_line_ids.filtered(
                        lambda l: (l.account_move_id.id == invoice.id))
                    _invoice_untaxed_amount = 0
                    _invoice_tax_amount = 0
                    _invoice_amount_total = 0
                    for li in _line_selected_in_invoice:
                        _invoice_untaxed_amount += li.untaxed_amount
                        _invoice_tax_amount += li.tax_amount
                        _invoice_amount_total += li.line_amount

                    if invoice.x_voucher_tax_transfer == 'custom_tax' \
                            and len(_line_selected_in_invoice) == len(_all_line_selected_in_invoice):
                        _invoice_tax_amount += invoice.amount_tax
                        _invoice_amount_total += invoice.amount_tax

                    # Create data fro bill_invoice table
                    _bill_invoice_ids = self.env['bill.invoice'].create({
                        'bill_info_id': _bill_info_ids.id,
                        'billing_code': self.billing_code,
                        'billing_name': self.billing_name,
                        'bill_no': _bill_no,
                        'bill_date': date.today(),
                        'last_closing_date': self.last_closing_date,
                        'closing_date': self.deadline,
                        'deadline': self.deadline,
                        'customer_code': invoice.partner_id.customer_code,
                        'customer_name': invoice.partner_id.name,
                        'amount_untaxed': _invoice_untaxed_amount,
                        'amount_tax': _invoice_tax_amount,
                        'amount_total': _invoice_amount_total,
                        'customer_trans_classification_code': invoice.customer_trans_classification_code,
                        'account_move_id': invoice.id,
                        'hr_employee_id': self.billing_place_id.customer_agent.id,
                        'hr_department_id': self.billing_place_id.customer_agent.department_id.id,
                        'business_partner_group_custom_id': self.billing_place_id.customer_supplier_group_code.id,
                        'customer_closing_date_id': self.billing_place_id.customer_closing_date.id,
                        'x_voucher_tax_transfer': invoice.x_voucher_tax_transfer,
                        'invoice_date': invoice.x_studio_date_invoiced,
                        'invoice_no': invoice.x_studio_document_no,
                        'x_studio_summary': invoice.x_studio_summary,
                    })
                    if len(_line_selected_in_invoice) == len(_all_line_selected_in_invoice):
                        # Update bill_status for records in account_move_line table
                        invoice.write({
                            'bill_status': 'billed'
                        })
                # Create data for bill_invoice_details table
                self.env['bill.invoice.details'].create({
                    'bill_info_id': _bill_info_ids.id,
                    'bill_invoice_id': _bill_invoice_ids and _bill_invoice_ids.id or False,
                    'billing_code': self.billing_code,
                    'billing_name': self.billing_name,
                    'bill_no': _bill_no,
                    'bill_date': date.today(),
                    'last_closing_date': self.last_closing_date,
                    'closing_date': self.deadline,
                    'deadline': self.deadline,
                    'customer_code': line.customer_code,
                    'customer_name': line.customer_name,
                    'customer_trans_classification_code': line.account_move_id.customer_trans_classification_code,
                    'account_move_line_id': line.account_move_line_id.id,
                    'hr_employee_id': line.partner_id.customer_agent.id,
                    'hr_department_id': line.partner_id.customer_agent.department_id.id,
                    'business_partner_group_custom_id': line.partner_id.customer_supplier_group_code.id,
                    'customer_closing_date_id': line.partner_id.customer_closing_date.id,
                    'x_voucher_tax_transfer': line.account_move_id.x_voucher_tax_transfer,
                    'invoice_date': line.invoice_date,
                    'invoice_no': line.invoice_no,
                    'tax_rate': line.account_move_line_id.tax_rate,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'tax_amount': line.tax_amount,
                    'line_amount': line.line_amount,
                    'voucher_line_tax_amount': line.account_move_line_id.voucher_line_tax_amount,
                })
                if line.payment_id:
                    # Update field bill_status and fields state for records in account_payment table
                    line.payment_id.write({
                        'bill_status': 'billed'
                    })
                    line.payment_id.post()
                else:
                    # Update bill_status for records in account_move_line table
                    line.account_move_line_id.write({
                        'bill_status': 'billed'
                    })
            self.last_billed_amount = _billed_amount
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
