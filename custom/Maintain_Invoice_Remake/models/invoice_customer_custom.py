# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from suds.client import Client
import json
import uuid
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import timedelta
from odoo.exceptions import ValidationError
import time
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re
import calendar
import math
import decimal

# forbidden fields
INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')


def calc_check_digits(number):
    """Calculate the extra digits that should be appended to the number to make it a valid number.
    Source: python-stdnum iso7064.mod_97_10.calc_check_digits
    """
    number_base10 = ''.join(str(int(x, 36)) for x in number)
    checksum = int(number_base10) % 97
    return '%02d' % ((98 - 100 * checksum) % 97)


def get_tax_method(tax_category=None, tax_unit=None):
    # # 消費税区分 = ３．非課税 or 消費税区分 is null or 消費税計算区分 is null ==> 税転嫁 = 非課税
    # if (tax_category == 'exempt') or (not tax_category) or (not tax_unit):
    #     return 'no_tax'
    # else:
    #     # 消費税計算区分 = １．明細単位
    #     if tax_unit == 'detail':
    #         # 消費税区分 = １．外税 ==> 税転嫁 = 外税／明細
    #         if tax_category == 'foreign':
    #             return 'foreign_tax'
    #         # 消費税区分 = 2．内税 ==> 税転嫁 = 内税／明細
    #         else:
    #             return 'internal_tax'
    #     # 消費税計算区分 = ２．伝票単位、３．請求単位 ==> 税転嫁 = 伝票、請求
    #     else:
    #         return tax_unit

    tax_method = 'foreign_tax'
    if tax_unit:
        if tax_unit == 'detail':
            tax_method = 'foreign_tax'
        else:
            tax_method = tax_unit

    return tax_method


def rounding(number, pre=0, type_rounding='round'):
    """Rounding number by type rounding(round, roundup, rounddown)."""
    if number != 0:
        multiplier = 10 ** pre
        if type_rounding == 'roundup':
            return math.ceil(number * multiplier) / multiplier
        elif type_rounding == 'rounddown':
            return math.floor(number * multiplier) / multiplier
        else:
            if pre < 0:
                return round(number, pre)
            else:
                context = decimal.getcontext()
                context.rounding = decimal.ROUND_HALF_UP
                return float(round(decimal.Decimal(number), pre))
    else:
        return 0


# Copy data from partner
def copy_data_from_partner(rec, partner):
    if partner:
        rec.partner_id = partner
        rec.x_studio_name = partner.name
        rec.x_studio_address_1 = partner.street
        rec.x_studio_address_2 = partner.street2
        rec.x_studio_address_3 = partner.address3
        rec.sales_rep = partner.customer_agent
        rec.x_studio_payment_rule_1 = partner.payment_rule
        rec.x_studio_price_list = partner.property_product_pricelist
        rec.invoice_payment_terms_custom = partner.payment_terms
        rec.x_bussiness_partner_name_2 = partner.customer_name_kana
        rec.customer_tax_rounding = partner.customer_tax_rounding
        # Add customer info
        rec.customer_group = partner.customer_supplier_group_code.name
        rec.customer_state = partner.customer_state.name
        rec.customer_industry = partner.customer_industry_code.name
        rec.customer_trans_classification_code = partner.customer_trans_classification_code

        rec.x_voucher_tax_transfer = get_tax_method(tax_unit=partner.customer_tax_unit)

        # # set default 税転嫁 by 消費税区分 & 消費税計算区分
        # customer_tax_category = partner.customer_tax_category
        # customer_tax_unit = partner.customer_tax_unit
        #
        # # 消費税区分 = ３．非課税 or 消費税区分 is null or 消費税計算区分 is null ==> 税転嫁 = 非課税
        # if (customer_tax_category == 'exempt') or (not customer_tax_category) or (not customer_tax_unit):
        #     rec.x_voucher_tax_transfer = 'no_tax'
        # else:
        #     # 消費税計算区分 = １．明細単位
        #     if customer_tax_unit == 'detail':
        #         # 消費税区分 = １．外税 ==> 税転嫁 = 外税／明細
        #         if customer_tax_category == 'foreign':
        #             rec.x_voucher_tax_transfer = 'foreign_tax'
        #         # 消費税区分 = 2．内税 ==> 税転嫁 = 内税／明細
        #         else:
        #             rec.x_voucher_tax_transfer = 'internal_tax'
        #     # 消費税計算区分 = ２．伝票単位、３．請求単位 ==> 税転嫁 = 伝票、請求
        #     else:
        #         rec.x_voucher_tax_transfer = customer_tax_unit


# Copy data for lines from quotation
def copy_data_from_quotation(rec, quotation, account):
    if quotation:
        rec.invoice_line_ids = ()
        invoice_line_ids = []
        line_ids = []

        for line in rec.invoice_line_ids:
            line.move_id = ''
            # line.unlink()

        for line in rec.line_ids:
            line.move_id = ''
            # line.unlink()

        # Copy line
        for line in rec.trigger_quotation_history.order_line:
            if line.product_id:
                invoice_line_ids.append((0, False, {
                    'product_id': line.product_id,
                    'product_barcode': line.product_barcode,
                    'product_name': line.product_name,
                    'product_name2': line.product_name2,
                    'invoice_custom_standardnumber': line.product_standard_number,
                    'product_maker_name': line.product_maker_name,
                    'quantity': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'product_uom_id': line.product_uom_id,
                    'invoice_custom_lineamount': line.line_amount,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount,
                    'account_id': account.id,
                    'price_include_tax': line.price_include_tax,
                    'price_no_tax': line.price_no_tax
                }))

        rec.invoice_line_ids = invoice_line_ids
        rec.line_ids = line_ids


class ClassInvoiceCustom(models.Model):
    _inherit = 'account.move'

    # start register payment for payment_custom

    # _sql_constraints = [
    #     ('mail_followers_res_partner_res_model_id_uniq', 'unique(id, res_model,res_id,partner_id)',
    #      'Error, a partner cannot follow twice the same object.')
    # ]

    def _get_payment_vals(self):
        return {
            # 'partner_type': 'supplier',
            # 'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'partner_payment_address1': self.x_studio_address_1,
            'partner_payment_address2': self.x_studio_address_2,
            'collection_method_date': self.invoice_payment_terms_custom.payment_term_custom_fix_month_day,
            'collection_method_month': self.invoice_payment_terms_custom.payment_term_custom_fix_month_offset,
            'payment_method_id': 1,
            'amount': self.amount_total,
            'account_invoice_id': self.id
        }

    def expense_post_payment(self):
        self.ensure_one()
        company = self.company_id
        self = self.with_context(force_company=company.id, company_id=company.id)
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])

        # Create payment and post it
        payment = self.env['account.payment'].create(self._get_payment_vals())
        payment.post()

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        # account_move_lines_to_reconcile = self.env['account.move.line']
        # for line in payment.move_line_ids:
        #     if line.account_id.internal_type == 'payable' and not line.reconciled:
        #         account_move_lines_to_reconcile |= line
        # account_move_lines_to_reconcile.reconcile()

        if self.id:
            query = "UPDATE account_move " \
                    "SET invoice_payment_state='paid'" \
                    "WHERE id=%s "
            params = [self.id]
            self._cr.execute(query, params)

        return {'type': 'ir.actions.act_window_close'}

    # end register payment for payment_custom

    invoice_line_ids_tax = fields.One2many('account.tax.line', 'move_id', string='Invoice lines', index=True,
                                           auto_join=True, help="The move of this entry line.")

    def _get_default_partner_id(self):
        return self.env["res.partner"].search([], limit=1, order='id').id

    def _get_default_organization_id(self):
        return self.env["res.company"].search([], limit=1, order='id').id

    def _get_default_client_id(self):
        return self.env["res.company"].search([], limit=1, order='id').id

    def _get_default_target_doctype_id(self):
        return self.env["res.company"].search([], limit=1, order='id').id

    def _get_default_document_no(self):
        return self.env["account.payment"].search([], limit=1, order='id desc').name

    # 4明細 - (JPY)明細行合計:3,104.00 / 総合計: 3,104.00 = 3,104.00
    def get_default_num_line(self):
        # for l in self:
        amount_untaxed_format = "{:,.2f}".format(self.amount_untaxed)
        amount_total_format = "{:,.2f}".format(self.amount_total)
        return str(len(self.invoice_line_ids)) + '明細 - (JPY)明細行合計:' + str(amount_untaxed_format) + str(
            self.currency_id.symbol) + ' / 総合計:' \
               + str(amount_total_format) + str(self.currency_id.symbol) + ' = ' + str(amount_total_format) + str(
            self.currency_id.symbol)

    # get currency symbol
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)

    # Thay đổi tên hiển thị trên breadcum Invoices
    def _get_move_display_name(self, show_ref=False):
        ''' Helper to get the display name of an invoice depending of its type.
        :param show_ref:    A flag indicating of the display name must include or not the journal entry reference.
        :return:            A string representing the invoice.
        '''
        self.ensure_one()
        draft_name = ''
        if self.state == 'draft':
            draft_name += {
                'out_invoice': _('Draft Invoice'),
                'out_refund': _('Draft Credit Note'),
                'in_invoice': _('Draft Bill'),
                'in_refund': _('Draft Vendor Credit Note'),
                'out_receipt': _('Draft Sales Receipt'),
                'in_receipt': _('Draft Purchase Receipt'),
                'entry': _('Draft Entry'),
            }[self.type]
            if not self.name or self.name == '/':
                if self.type == 'out_invoice':
                    draft_name += ' / %s' % str(self.x_studio_document_no)
                else:
                    draft_name += ' (* %s)' % str(self.id)
            else:
                if self.type == 'out_invoice':
                    draft_name += ' ' + self.x_studio_document_no
                else:
                    draft_name += ' ' + self.name
        # trường hợp state
        if self.state == 'posted':
            if not self.name or self.name == '/':
                if self.type == 'out_invoice':
                    draft_name += ' / %s' % str(self.x_studio_document_no)
                else:
                    draft_name += ' (* %s)' % str(self.id)
            else:
                if self.type == 'out_invoice':
                    draft_name += ' ' + self.x_studio_document_no
                else:
                    draft_name += ' ' + self.name

        return (draft_name or self.name) + (
                show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')

    # Calculate due date
    def _get_due_date(self):
        if self.x_studio_date_invoiced:
            offset_month = self.invoice_payment_terms_custom.payment_term_custom_fix_month_offset
            cutoff_day = self.invoice_payment_terms_custom.payment_term_custom_fix_month_cutoff
            payment_day = self.invoice_payment_terms_custom.payment_term_custom_fix_month_day
            invoice_year = self.x_studio_date_invoiced.year
            invoice_month = self.x_studio_date_invoiced.month

            # Check if is correct day
            try:
                cutoff_date = date(invoice_year, invoice_month, cutoff_day)
            except ValueError:
                cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                cutoff_date = date(invoice_year, invoice_month, cutoff_day)

            # Payment date
            temp_date = cutoff_date + relativedelta(months=offset_month)

            try:
                due_date = date(temp_date.year, temp_date.month, payment_day)
            except ValueError:
                due_date = self.x_studio_date_invoiced

            return due_date

        return False

    # Compute line len
    def get_line_len(self):
        return len(self.invoice_line_ids)

    @api.onchange('state')
    def _get_printed_boolean(self):
        self.x_studio_printed = self.state == 'posted'

    @api.model
    def _get_latest_document_no(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'document.sequence')])
        next = sequence.get_next_char(sequence.number_next_actual)
        return next

    x_studio_client_2 = fields.Many2one('client.custom', string='Client', default=_get_default_client_id)
    x_studio_organization = fields.Many2one('res.company', default=_get_default_organization_id)
    x_studio_business_partner = fields.Many2one('res.partner', 'Customer')
    x_studio_name = fields.Char('name')
    x_studio_address_1 = fields.Char('address 1')
    x_studio_address_2 = fields.Char('address 2')
    x_studio_address_3 = fields.Char('address 3')
    search_key = fields.Char('search key')
    x_studio_target_doc_type = fields.Many2one('account.journal', default=_get_default_target_doctype_id)
    x_studio_document_no = fields.Char(string="Document No", readonly=True, copy=False, default=_get_latest_document_no)
    invoice_document_no_custom = fields.Char(string="Document", readonly=True, copy=False,
                                             default=_get_default_document_no)
    x_studio_cus_salesslipforms_table = fields.Selection([('cus_1', '指定なし'), ('cus_2', '通常'), ('cus_3', '専伝・仮伝')])
    x_studio_date_invoiced = fields.Date(string='Invoice Date', default=date.today())
    x_studio_date_printed = fields.Date(string='Date Printed', default=date.today())
    x_studio_date_shipment = fields.Date(string='Shipment Date', default=date.today())
    x_current_date = fields.Date(string='', default=date.today(), store=False)
    x_studio_payment_rule_1 = fields.Selection([('rule_cash', 'Cash'), ('rule_check', 'Check'),
                                                ('rule_credit', 'Credit Card'), ('rule_direct_debit', 'Direct Debit'),
                                                ('rule_deposit', 'Direct Deposit'), ('rule_on_credit', 'On Credit')],
                                               'payment rule', default='rule_on_credit')
    # partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
    #                              states={'draft': [('readonly', False)]},
    #                              domain="[('customer_rank','=', 1)]",
    #                              string='Partner', change_default=True)
    invoice_payment_terms_custom = fields.Many2one('account.payment.term')
    write_date = fields.Date('updated')
    create_date = fields.Date('create_date')
    x_studio_printed = fields.Boolean('printed', compute=_get_printed_boolean)
    invoice_total_paid = fields.Monetary('invoice_total_paid', compute='_compute_invoice_total_paid')

    x_studio_line_info = fields.Char('', default=get_default_num_line, store=False)
    x_due_date = fields.Date('', default=_get_due_date, store=False)
    line_len = fields.Integer('', default=get_line_len, store=False)

    x_transaction_type = fields.Selection([('掛売', '掛売'), ('現金売', '現金売')], default='掛売')
    x_voucher_tax_amount = fields.Monetary('Voucher Tax Amount')
    # x_voucher_deadline = fields.Selection([('今回', '次回','通常','来月勘定'), ('今回', '次回','通常','来月勘定')],default='今回')
    x_voucher_tax_transfer = fields.Selection([
        ('foreign_tax', '外税／明細'),
        ('internal_tax', '内税／明細'),
        ('voucher', '伝票'),
        ('invoice', '請求'),
        ('custom_tax', '税調整別途')
    ], string='Tax Transfer', default='foreign_tax')

    # 消費税端数処理
    customer_tax_rounding = fields.Selection(
        [('round', 'Rounding'), ('roundup', 'Round Up'), ('rounddown', 'Round Down')],
        string='Tax Rounding', default='round')
    # from customer master
    customer_office = fields.Char('Customer Office', compute='get_office')
    customer_group = fields.Char('Customer Group')
    customer_state = fields.Char('Customer State')
    customer_industry = fields.Char('Customer Industry')
    customer_closing_date = fields.Date('Closing Date')
    customer_from_date = fields.Date('customer_from_date')
    customer_trans_classification_code = fields.Selection([('sale', '掛売'), ('cash', '現金'), ('account', '諸口')],
                                                          string='Transaction Class', default='sale')
    closing_date_compute = fields.Integer('Temp')
    x_customer_code_for_search = fields.Char('Customer Code', related='x_studio_business_partner.customer_code')
    x_voucher_deadline = fields.Selection([('今回', '今回'), ('次回', '次回')], default='今回')
    x_bussiness_partner_name_2 = fields.Char('名称2')
    x_studio_description = fields.Text('説明')
    x_userinput_id = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.uid)
    related_userinput_name = fields.Char('Sales rep name', related='x_userinput_id.name')
    x_history_voucher = fields.Many2one('account.move', string='Journal Entry',
                                        index=True, auto_join=True,
                                        help="The moveview_move_custom_form of this entry line.")
    sales_rep = fields.Many2one('hr.employee', string='Sales Rep')
    related_sale_rep_name = fields.Char('Sales rep name', related='sales_rep.name')

    # Field for trigger onchange when fill data
    # Just to trigger to change data, not store
    trigger_quotation_history = fields.Many2one('sale.order', store=False)

    # get payment_amount from account_payment
    amount_from_payment = fields.Float(string='Amount from payment')

    @api.onchange('trigger_quotation_history')
    def _compute_fill_data_with_quotation(self):
        account = self.env.company.get_chart_of_accounts_or_fail()

        for rec in self:
            if rec.trigger_quotation_history:
                # Call method to set data for lines
                copy_data_from_quotation(rec, rec.trigger_quotation_history, account)

                # Form info
                rec.x_studio_business_partner = rec.trigger_quotation_history.partner_id

                # Call method to set data when change partner
                copy_data_from_partner(rec, rec.x_studio_business_partner)

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.x_invoicelinetype',
        'x_voucher_tax_transfer',
        'customer_tax_rounding')
    def _compute_amount(self):
        invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]
        self.env['account.payment'].flush(['state'])
        if invoice_ids:
            self._cr.execute(
                '''
                    SELECT move.id
                    FROM account_move move
                    JOIN account_move_line line ON line.move_id = move.id
                    JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                    JOIN account_move_line rec_line ON
                        (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
                        OR
                        (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
                    JOIN account_payment payment ON payment.id = rec_line.payment_id
                    JOIN account_journal journal ON journal.id = rec_line.journal_id
                    WHERE payment.state IN ('posted', 'sent')
                    AND journal.post_at = 'bank_rec'
                    AND move.id IN %s
                ''', [tuple(invoice_ids)]
            )
            in_payment_set = set(res[0] for res in self._cr.fetchall())
        else:
            in_payment_set = {}

        for move in self:
            total_voucher_tax_amount = 0.0
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = set()
            total_untaxed_custom = 0.0

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)

                if move.is_invoice(include_receipts=True):
                    # === Invoices ===
                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        if line.x_invoicelinetype != 'サンプル':
                            if move.x_voucher_tax_transfer == 'voucher' \
                                    and line.product_id.product_tax_category != 'exempt':
                                # total_line_tax = sum(
                                #     tax.amount for tax in line.tax_ids._origin.flatten_taxes_hierarchy())
                                line_tax_amount = (line.tax_rate * line.price_unit * line.quantity) / 100

                                total_voucher_tax_amount += line_tax_amount
                            else:
                                total_voucher_tax_amount += line.line_tax_amount
                            total_untaxed_custom += line.invoice_custom_lineamount
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1

            if move.x_voucher_tax_transfer != 'custom_tax':
                if move.x_voucher_tax_transfer == 'voucher':
                    move.x_voucher_tax_amount = rounding(total_voucher_tax_amount, 2, move.customer_tax_rounding)
                else:
                    move.x_voucher_tax_amount = total_voucher_tax_amount
            # else:
            #     move.x_voucher_tax_amount = move.x_voucher_tax_amount

            # move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            # move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            # move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            move.amount_untaxed = total_untaxed_custom
            move.amount_tax = move.x_voucher_tax_amount
            move.amount_total = move.amount_untaxed + move.amount_tax
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.type == 'entry' else -total
            move.amount_residual_signed = total_residual

            currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
            is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual

            # Compute 'invoice_payment_state'.
            if move.type == 'entry':
                move.invoice_payment_state = False
            elif move.state == 'posted' and is_paid:
                if move.id in in_payment_set:
                    move.invoice_payment_state = 'in_payment'
                else:
                    move.invoice_payment_state = 'paid'
            else:
                move.invoice_payment_state = 'not_paid'

    @api.onchange('x_voucher_tax_amount')
    def _onchange_amount_tax(self):
        self._compute_amount()

    @api.onchange('x_history_voucher')
    def _onchange_x_test(self):
        for voucher in self:
            result_l1 = []
            result_l2 = []
            voucher.line_ids = ()
            voucher.invoice_line_ids = ()

            # print(voucher.x_history_voucher.invoice_line_ids)
            for l in voucher.x_history_voucher.invoice_line_ids:
                fields_line = l.fields_get()
                line_data = {attr: getattr(l, attr) for attr in fields_line}
                del line_data['move_id']
                result_l1.append((0, False, line_data))

            # for l in voucher.x_history_voucher.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab):
            for l in voucher.x_history_voucher.line_ids:
                fields_line = l.fields_get()
                line_data = {attr: getattr(l, attr) for attr in fields_line}
                del line_data['move_id']
                result_l2.append((0, False, line_data))
            if voucher.x_history_voucher._origin.id:
                voucher.x_studio_business_partner = voucher.x_history_voucher.x_studio_business_partner
                voucher.partner_id = voucher.x_studio_business_partner

                voucher.x_studio_client_2 = voucher.x_history_voucher.x_studio_client_2
                voucher.x_studio_organization = voucher.x_history_voucher.x_studio_organization
                voucher.x_studio_name = voucher.x_history_voucher.x_studio_name
                voucher.x_studio_address_1 = voucher.x_history_voucher.x_studio_address_1
                voucher.x_studio_address_2 = voucher.x_history_voucher.x_studio_address_2
                voucher.x_studio_address_3 = voucher.x_history_voucher.x_studio_address_3
                voucher.search_key = voucher.x_history_voucher.search_key
                voucher.x_studio_target_doc_type = voucher.x_history_voucher.x_studio_target_doc_type
                voucher.invoice_document_no_custom = voucher.x_history_voucher.invoice_document_no_custom
                voucher.x_studio_cus_salesslipforms_table = voucher.x_history_voucher.x_studio_cus_salesslipforms_table
                voucher.x_studio_date_invoiced = voucher.x_history_voucher.x_studio_date_invoiced
                voucher.x_studio_date_printed = voucher.x_history_voucher.x_studio_date_printed
                voucher.x_studio_date_shipment = voucher.x_history_voucher.x_studio_date_shipment
                voucher.x_current_date = voucher.x_history_voucher.x_current_date
                voucher.x_studio_payment_rule_1 = voucher.x_history_voucher.x_studio_payment_rule_1
                voucher.invoice_payment_terms_custom = voucher.x_history_voucher.invoice_payment_terms_custom
                voucher.x_studio_printed = voucher.x_history_voucher.x_studio_printed
                voucher.invoice_total_paid = voucher.x_history_voucher.invoice_total_paid
                voucher.x_studio_line_info = voucher.x_history_voucher.x_studio_line_info
                voucher.x_due_date = voucher.x_history_voucher.x_due_date
                voucher.line_len = voucher.x_history_voucher.line_len
                voucher.x_transaction_type = voucher.x_history_voucher.x_transaction_type
                voucher.x_voucher_tax_amount = voucher.x_history_voucher.x_voucher_tax_amount
                voucher.x_studio_description = voucher.x_history_voucher.x_studio_description
                voucher.x_studio_price_list = voucher.x_history_voucher.x_studio_price_list
                voucher.x_bussiness_partner_name_2 = voucher.x_history_voucher.x_bussiness_partner_name_2
                voucher.x_voucher_tax_transfer = voucher.x_history_voucher.x_voucher_tax_transfer
                voucher.customer_tax_rounding = voucher.x_history_voucher.customer_tax_rounding
            voucher.line_ids = result_l2
            voucher.invoice_line_ids = result_l1

        # self._set_tax_counting()
        # self._onchange_invoice_line_ids()

    def action_view_form_modelname(self):
        view = self.env.ref('Maintain_Invoice_Remake.view_move_custom_form')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.onchange('x_studio_business_partner')
    def _get_detail_business_partner(self):
        for rec in self:
            copy_data_from_partner(rec, rec.x_studio_business_partner)

            # # call onchange of 税転嫁
            # if rec.x_voucher_tax_transfer:
            #     self._set_tax_counting()

    # @api.onchange('x_voucher_tax_transfer')
    # def _set_tax_counting(self):
    #     self._onchange_invoice_line_ids()
    #     for line in self.invoice_line_ids:
    #         line._onchange_product_id()
    #         line._onchange_price_subtotal()

    # Get customer office
    def get_office(self):
        for rec in self:
            temp = ''
            partner = rec.x_studio_business_partner
            for line in partner.relation_id:
                if line.relate_related_partner.name:
                    temp = line.relate_related_partner.name
                    # break
            rec.customer_office = temp

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        current_invoice_lines = self.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)
        others_lines = self.line_ids - current_invoice_lines
        if others_lines and current_invoice_lines - self.invoice_line_ids:
            others_lines[0].recompute_tax_line = True
        self.line_ids = others_lines + self.invoice_line_ids
        self._onchange_recompute_dynamic_lines()

    @api.onchange('x_studio_payment_rule_1')
    def _get_payment_terms_by_rules(self):
        for rec in self:
            if rec.x_studio_business_partner:
                rec.invoice_payment_terms_custom = rec.x_studio_business_partner.payment_terms
            elif self.x_studio_payment_rule_1 == 'rule_cash' \
                    or self.x_studio_payment_rule_1 == 'rule_check' \
                    or self.x_studio_payment_rule_1 == 'rule_credit' \
                    or self.x_studio_payment_rule_1 == 'rule_direct_debit' \
                    or self.x_studio_payment_rule_1 == 'rule_deposit' \
                    or self.x_studio_payment_rule_1 == 'rule_on_credit':
                self.invoice_payment_terms_custom = 1

    @api.constrains('x_studio_date_invoiced', 'invoice_line_ids', 'x_studio_business_partner')
    def _change_date_invoiced(self):
        for line in self.invoice_line_ids:
            line.date = self.x_studio_date_invoiced
            line.partner_id = self.x_studio_business_partner

    # tính ngày closing date dựa theo start day của customer
    @api.onchange('closing_date_compute', 'x_studio_date_invoiced', 'x_voucher_deadline', 'x_studio_business_partner')
    def _get_closing_date(self):
        for rec in self:
            rec.closing_date_compute = rec.x_studio_business_partner.customer_closing_date.start_day
            # day = int(rec.x_studio_date_invoiced.strftime('%d'))
            if rec.x_studio_date_invoiced:
                day = int(rec.x_studio_date_invoiced.strftime('%d'))
                closing_date = rec.closing_date_compute
                invoice_year = rec.x_studio_date_invoiced.year
                invoice_month = rec.x_studio_date_invoiced.month
                if int(day) > int(rec.closing_date_compute):
                    if rec.x_voucher_deadline == '今回':
                        try:
                            rec.customer_closing_date = date(invoice_year, invoice_month, closing_date) + relativedelta(
                                months=1)
                        except ValueError:
                            cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                            rec.customer_closing_date = date(invoice_year, invoice_month, cutoff_day) + relativedelta(
                                months=1)
                    else:
                        try:
                            rec.customer_closing_date = date(invoice_year, invoice_month, closing_date) + relativedelta(
                                months=2)
                        except ValueError:
                            cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                            rec.customer_closing_date = date(invoice_year, invoice_month, cutoff_day) + relativedelta(
                                months=2)
                else:
                    if rec.x_voucher_deadline == '今回':
                        try:
                            rec.customer_closing_date = date(invoice_year, invoice_month, closing_date)
                        except ValueError:
                            cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                            rec.customer_closing_date = date(invoice_year, invoice_month, cutoff_day)

                    else:
                        try:
                            rec.customer_closing_date = date(invoice_year, invoice_month, closing_date) + relativedelta(
                                months=1)
                        except ValueError:
                            cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                            rec.customer_closing_date = date(invoice_year, invoice_month, cutoff_day) + relativedelta(
                                months=1)

            day = int(rec.customer_closing_date.strftime('%d'))
            year = rec.customer_closing_date.year
            month = rec.customer_closing_date.month

            rec.customer_from_date = date(year, month, day) - relativedelta(months=1) - relativedelta(days=1)

    @api.constrains('x_studio_date_invoiced')
    def _validate_plate(self):
        res = self.env['account.move'].sudo().search([('x_studio_date_invoiced', '=', self.x_studio_date_invoiced)])
        if not res.company_id:
            raise ValidationError('You must choose invoice date!')

    @api.model
    def create(self, vals):
        if vals.get('x_studio_document_no', _('0')) == _('0'):
            vals['x_studio_document_no'] = self.env['ir.sequence'].next_by_code('document.sequence') or _('New')
        result = super(ClassInvoiceCustom, self).create(vals)
        return result

    # lấy thông tin office từ khách hàng
    def _compute_get_customer_office(self):
        for rec in self:
            temp = ''
            partner = rec.x_studio_business_partner
            for line in partner.relation_id:
                if line.relate_related_partner.name:
                    temp = line.relate_related_partner.name
                    break
            rec.customer_office = temp

    # tính tiền khách trả trước
    def _compute_invoice_total_paid(self):
        for rec in self:
            if rec.state == 'posted':
                rec.invoice_total_paid = rec.amount_total - rec.amount_residual
            else:
                rec.invoice_total_paid = 0

    def _compute_invoice_taxes_by_group(self):
        ''' Helper to get the taxes grouped according their account.tax.group.
        This method is only used when printing the invoice.
        '''
        for move in self:
            lang_env = move.with_context(lang=move.partner_id.lang).env
            tax_lines = move.line_ids.filtered(lambda line: line.tax_line_id)
            res = {}
            # There are as many tax line as there are repartition lines
            done_taxes = set()
            result = []
            item = {}
            count = 0
            # self.env["account.tax.line"].search([('move_id', '=', move.id)]).unlink()
            # print(move.id)
            tax_base_amount = 0.00
            tax_amount = 0.00
            for line in move.invoice_line_ids:
                tax_base_amount += line.invoice_custom_lineamount
                tax_amount += line.line_tax_amount

            self.invoice_line_ids_tax = [(5, 0, 0)]
            for line in tax_lines:
                res.setdefault(line.tax_line_id.tax_group_id, {'base': 0.0, 'amount': 0.0})
                # res[line.tax_line_id.tax_group_id]['amount'] += line.price_subtotal
                res[line.tax_line_id.tax_group_id]['amount'] = tax_amount
                tax_key_add_base = tuple(move._get_tax_key_for_group_add_base(line))
                if tax_key_add_base not in done_taxes:
                    if line.currency_id != self.company_id.currency_id:
                        amount = self.company_id.currency_id._convert(line.tax_base_amount, line.currency_id,
                                                                      self.company_id, line.date or fields.Date.today())
                    else:
                        amount = line.tax_base_amount

                    # res[line.tax_line_id.tax_group_id]['base'] += amount
                    res[line.tax_line_id.tax_group_id]['base'] = tax_base_amount
                    # The base should be added ONCE
                    done_taxes.add(tax_key_add_base)
            print(res.keys())
            for x in res:
                result.append(
                    (0, False, {'move_id': move.id, 'move_name': self.x_studio_document_no, 'taxGroup': x.name,
                                'tax_base_amount': res[x]['base'], 'tax_amount': res[x]['amount']}))
                # self.invoice_line_ids_tax = [
                #     (0, False, {'move_id': move.id, 'move_name': move.name, 'taxGroup': x.name, 'tax_base_amount': res[x]['base'],'tax_amount':res[x]['amount']})]
                #     (0, False, {'move_id': move.id, 'move_name': move.name, 'taxGroup': x.name})]
            print(result)
            self.invoice_line_ids_tax = result
            # At this point we only want to keep the taxes with a zero amount since they do not
            # generate a tax line.
            for line in move.line_ids:
                for tax in line.tax_ids.filtered(lambda t: t.amount == 0.0):
                    # print('test2')
                    res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})
                    res[tax.tax_group_id]['base'] += line.price_subtotal

            res = sorted(res.items(), key=lambda l: l[0].sequence)
            move.amount_by_group = [(
                group.name, amounts['amount'],
                amounts['base'],
                formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id),
                formatLang(lang_env, amounts['base'], currency_obj=move.currency_id),
                len(res),
                group.id
            ) for group, amounts in res]

            move.x_studio_line_info = move.get_default_num_line()
            move.line_len = move.get_line_len()

    def _get_reconciled_info_JSON_values(self):
        self.ensure_one()
        foreign_currency = self.currency_id if self.currency_id != self.company_id.currency_id else False

        reconciled_vals = []
        pay_term_line_ids = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        partials = pay_term_line_ids.mapped('matched_debit_ids') + pay_term_line_ids.mapped('matched_credit_ids')
        for partial in partials:
            counterpart_lines = partial.debit_move_id + partial.credit_move_id
            counterpart_line = counterpart_lines.filtered(lambda line: line not in self.line_ids)

            if foreign_currency and partial.currency_id == foreign_currency:
                amount = partial.amount_currency
            else:
                amount = partial.company_currency_id._convert(partial.amount, self.currency_id, self.company_id,
                                                              self.date)

            if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                continue

            if len(counterpart_line.move_id) > 1:
                return reconciled_vals

            if counterpart_line.move_id:
                ref = counterpart_line.move_id.name
                if counterpart_line.move_id.ref:
                    ref += ' (' + counterpart_line.move_id.ref + ')'

                reconciled_vals.append({
                    'name': counterpart_line.name,
                    'journal_name': counterpart_line.journal_id.name,
                    'amount': amount,
                    'currency': self.currency_id.symbol,
                    'digits': [69, self.currency_id.decimal_places],
                    'position': self.currency_id.position,
                    'date': counterpart_line.date,
                    'payment_id': counterpart_line.id,
                    'account_payment_id': counterpart_line.payment_id.id,
                    'payment_method_name': counterpart_line.payment_id.payment_method_id.name if counterpart_line.journal_id.type == 'bank' else None,
                    'move_id': counterpart_line.move_id.id,
                    'ref': ref,
                })
        return reconciled_vals

    # @api.model
    # def name_search1(self):
    #     return {
    #         'name': _('test'),
    #         'view_type': 'tree',
    #         'view_mode': 'tree',
    #         'view_id': 'self.env.ref('account.move').id',
    #         'res_model': 'account.move',
    #         'context': "{'type':'out_invoice'}",
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #     }

    def action_confirm(self):
        print('click aaaaaaaaaaaaaaaaa')
        for order in self:
            # params = order.check_credit_limit()
            # view_id = self.env['sale.control.limit.wizard']
            # new = view_id.create(params[0])
            return {
                'type': 'ir.actions.act_window',
                'name': 'Warning : Customer is about or exceeded their credit limit',
                'res_model': 'account.move',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': id,
                'view_id': self.env.ref('Maintain_Invoice_Remake.view_move_custom_form', False).id,
                'target': 'new',
            }

    def button_sale_history(self):
        view = {
            'name': _('Invoice Lines'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            # 'readonly': False,
            # 'create': True,
            'res_id': self.id,
        }
        return view

    # Get lines
    # Method will be call when click on button (.O_button_line) show line in tree view
    def get_lines(self):
        records = self.env['account.move.line'].search([
            ('move_id', 'in', self._ids),
            ('product_id', '!=', False)
        ], order='invoice_custom_line_no').read()

        # Get tax
        for record in records:
            if record['tax_ids']:
                self._cr.execute('''
                                    SELECT id, name
                                    FROM account_tax
                                    WHERE id IN %s
                                ''', [tuple(record['tax_ids'])])
                query_res = self._cr.fetchall()
                record['tax_ids'] = ', '.join([str(res[1]) for res in query_res])

        return {
            'template': 'invoice_lines',
            'records': records
        }

    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(['debit', 'credit', 'move_id'])
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(debit - credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(debit - credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if query_res:
            return
            # ids = [res[0] for res in query_res]
            # sums = [res[1] for res in query_res]
            # raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))


class AccountTaxLine(models.Model):
    _name = 'account.tax.line'
    move_name = fields.Char('Invoice')
    tax_base_amount = fields.Float('Tax base Amount')
    tax_amount = fields.Float('Tax Amount')
    price_include_tax = fields.Boolean('Price includes Tax', default=True)
    taxGroup = fields.Char('Tax')
    tax_provider = fields.Char('Tax Provider')
    move_id = fields.Many2one('account.move', string='Journal Entry',
                              index=True, readonly=True, auto_join=True,
                              help="The move of this entry line.")

    def _get_default_organization_id(self):
        return self.env["res.company"].search([], limit=1, order='id').id

    def _get_default_client_id(self):
        return self.env["res.company"].search([], limit=1, order='id').id

    client = fields.Many2one('client.custom', default=_get_default_client_id)
    organization = fields.Many2one('res.company', default=_get_default_organization_id)

    def button_update(self):
        view = {
            'name': _('Invoice Tax'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.tax.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': False,
            'create': True,
            'res_id': self.id,
        }
        return view


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange('x_history_detail')
    def _onchange_x_test(self):
        result_l1 = []
        result_l2 = []
        for line in self:
            print('line')
            print(line)
            detail_history = line.x_history_detail
            if detail_history.id:
                print('start set')

                line.x_invoicelinetype = detail_history.x_invoicelinetype
                line.product_barcode = detail_history.product_barcode
                line.x_product_modelnumber = detail_history.x_product_modelnumber
                line.product_name = detail_history.product_name
                line.product_name2 = detail_history.product_name2
                line.product_uom_id = detail_history.product_uom_id
                line.tax_rate = detail_history.tax_rate
                line.product_standard_price = detail_history.product_standard_price
                line.invoice_custom_standardnumber = detail_history.invoice_custom_standardnumber
                line.x_product_cost_price = detail_history.x_product_cost_price
                line.invoice_custom_discountunitprice = detail_history.invoice_custom_discountunitprice
                line.invoice_custom_discountrate = detail_history.invoice_custom_discountrate
                line.invoice_custom_lineamount = detail_history.invoice_custom_lineamount
                line.invoice_custom_Description = detail_history.invoice_custom_Description
                line.invoice_custom_salesunitprice = detail_history.invoice_custom_salesunitprice
                line.product_maker_name = detail_history.product_maker_name
                line.price_unit = detail_history.price_unit
                line.quantity = detail_history.quantity
                line.product_id = detail_history.product_id

    def get_default_line_no(self):
        context = dict(self._context or {})
        line_ids = context.get('default_line_ids')
        move_id = context.get('default_move_id')
        max1 = 0

        list_line = []
        if move_id:
            list_line = self.env["account.move.line"].search(
                [("move_id.id", "=", move_id), ("exclude_from_invoice_tab", "=", False)])

        # get all line in db and state draf
        list_final = {}
        if list_line is not None:
            for l_db in list_line:
                list_final[l_db.id] = l_db.invoice_custom_line_no
            if line_ids is not None:
                for l_v in line_ids:
                    # check state (delete,update,new,no change)
                    # 0: new
                    # 1: update
                    # 2: delete
                    # 4: no change
                    if l_v[0] == 0:
                        if 'exclude_from_invoice_tab' in l_v[2]:
                            if l_v[2]['exclude_from_invoice_tab'] == False:
                                list_final[l_v[1]] = l_v[2]['invoice_custom_line_no']
                    if l_v[0] == 1 and 'invoice_custom_line_no' in l_v[2]:
                        if 'exclude_from_invoice_tab' in l_v[2]:
                            if l_v[2]['exclude_from_invoice_tab'] == False:
                                list_final[l_v[1]] = l_v[2]['invoice_custom_line_no']
                    if l_v[0] == 2:
                        list_final[l_v[1]] = 0
        max = 0
        for id in list_final:
            if max < list_final[id]:
                max = list_final[id]
        return max + 1

    def generate_selection(self):
        return 'abc'

    @api.onchange('x_crm_purchased_products')
    def _onchange_x_crm_purchased_products(self):
        for p in self:
            p.x_crm_purchased_products._rec_name = 'aaaaaa'

    date = fields.Date(related='move_id.x_studio_date_invoiced', store=True, readonly=True, index=True, copy=False, group_operator='min')
    invoice_custom_line_no = fields.Integer('Line No', default=get_default_line_no)
    # Update 2020/04/28 - START
    x_invoicelinetype = fields.Selection([('通常', '通常'), ('返品', '返品'), ('値引', '値引'), ('サンプル', 'サンプル')],
                                         default='通常')
    product_barcode = fields.Char(string='JAN/UPC/EAN')
    product_uom_id = fields.Char(string='UoM')
    # product_barcode_show_in_tree = fields.Char(string='JANコード', related='product_barcode.barcode')
    # x_product_code_show_in_tree = fields.Char(string='商品コード', related='product_barcode.product_code_1')

    x_product_modelnumber = fields.Char('Product')
    product_name = fields.Text('mproductname')
    product_name2 = fields.Text('mproductname2')
    product_standard_price = fields.Float('Standard Price')
    x_product_cost_price = fields.Float('Cost Price')
    # x_crm_purchased_products = fields.Many2one('crm.purchased_products', selection='generate_selection', string='Purchased products')

    # Update 2020/04/28 - END
    invoice_custom_standardnumber = fields.Char('standardnumber')

    invoice_custom_discountunitprice = fields.Float('discountunitprice', compute='compute_discount_unit_price')
    invoice_custom_discountrate = fields.Float('discountrate')
    invoice_custom_salesunitprice = fields.Float('salesunitprice', compute='compute_sale_unit_price')
    invoice_custom_lineamount = fields.Float('Line Amount', compute='compute_line_amount')
    invoice_custom_Description = fields.Text('Description')
    # product_maker_name = fields.Many2one('freight.category.custom', string='Maker Code')
    product_maker_name = fields.Char(string='Maker Name')
    price_unit = fields.Float(string='Unit Price', digits='Product Price', compute="compute_price_unit", store="True")
    quantity = fields.Float(string='Quantity', digits='(12,0)',
                            default=1.0,
                            help="The optional quantity expressed by this line, eg: number of product sold. "
                                 "The quantity is not a legal requirement but is very useful for some reports.")

    move_id = fields.Many2one('account.move', string='Journal Entry',
                              index=True, required=True, readonly=True, auto_join=True,
                              help="The move of this entry line.")
    move_name = fields.Char(compute='compute_move_name')
    invoice_no = fields.Char(string='伝票Ｎｏ', related='move_id.x_studio_document_no', store=True, index=True)
    x_tax_transfer_show_tree = fields.Selection(string='税転嫁', related='move_id.x_voucher_tax_transfer', store=True,
                                                index=True)
    x_customer_show_in_tree = fields.Char(string='得意先名', compute='compute_x_customer_show_in_tree')
    x_history_detail = fields.Many2one('account.move.line', string='Journal Entry',
                                       index=True, auto_join=True,
                                       help="The move of this entry line.")

    line_tax_amount = fields.Float('Tax Amount', compute='compute_line_tax_amount')
    # line_tax_amount = fields.Float('Tax Amount')

    tax_rate = fields.Float('Tax Rate')
    product_code = fields.Char(string="Product Code")

    price_no_tax = fields.Float('Price No Tax')
    price_include_tax = fields.Float('Price Include Tax')
    temp_onchange_field = ''

    @api.onchange('product_code')
    def _onchange_product_code(self):
        if not self.temp_onchange_field:
            self.temp_onchange_field = 'product_code'

            if self.product_code:
                product = self.env['product.product'].search([
                    '|', '|', '|', '|', '|',
                    ['product_code_1', '=', self.product_code],
                    ['product_code_2', '=', self.product_code],
                    ['product_code_3', '=', self.product_code],
                    ['product_code_4', '=', self.product_code],
                    ['product_code_5', '=', self.product_code],
                    ['product_code_6', '=', self.product_code]
                ])

                if product:
                    self.product_id = product.id
                    self.product_barcode = product.barcode
                    setting_price = "1"
                    if self.product_code == product.product_code_2:
                        setting_price = "2"
                    elif self.product_code == product.product_code_3:
                        setting_price = "3"
                    elif self.product_code == product.product_code_4:
                        setting_price = "4"
                    elif self.product_code == product.product_code_5:
                        setting_price = "5"
                    elif self.product_code == product.product_code_6:
                        setting_price = "6"
                    if product.product_tax_category == 'exempt':
                        self.price_include_tax = self.price_no_tax = product["price_" + setting_price]
                    else:
                        self.price_include_tax = product["price_include_tax_" + setting_price]
                        self.price_no_tax = product["price_no_tax_" + setting_price]

                    self.price_unit = self._get_computed_price_unit()
                    return

            # else
            self.product_barcode = ''

    @api.onchange('product_barcode')
    def _onchange_product_barcode(self):
        if not self.temp_onchange_field:
            self.temp_onchange_field = 'product_barcode'

            if self.product_barcode:
                product = self.env['product.product'].search([
                    ['barcode', '=', self.product_barcode]
                ])

                if product:
                    self.product_id = product.id
                    self.product_code = product.code_by_setting
                    setting_price = '1'
                    if product.setting_price:
                        setting_price = product.setting_price[5:]
                    if product.product_tax_category == 'exempt':
                        self.price_include_tax = self.price_no_tax = product["price_" + setting_price]
                    else:
                        self.price_include_tax = product["price_include_tax_" + setting_price]
                        self.price_no_tax = product["price_no_tax_" + setting_price]
                    self.price_unit = self._get_computed_price_unit()
                    return

            # else:
            self.product_code = ''

    # # 消費税区分
    # line_tax_category = fields.Selection(
    #     [('foreign', 'Foreign Tax'), ('internal', 'Internal Tax'), ('exempt', 'Tax Exempt')],
    #     string='Tax Category', default='foreign')

    def compute_x_customer_show_in_tree(self):
        for line in self:
            line.x_customer_show_in_tree = line.move_id.x_studio_business_partner.name

    # def compute_product_barcode_show_in_tree(self):
    #     for line in self:
    #         line.product_barcode_show_in_tree = line.product_barcode.barcode
    #
    # def compute_product_code_show_in_tree(self):
    #     for line in self:
    #         line.x_product_code_show_in_tree = line.product_barcode.product_code_1

    def _validate_price_unit(self):
        for p in self:
            if p.price_unit < 0:
                # self.price_unit = self._origin.price_unit
                raise ValidationError(_("最小制限価格: " + str(p.price_unit) + ", PriceLimit=0"))
        return

    def _validate_discountrate(self):
        for p in self:

            if p.discount < 0:
                # self.discount = self._origin.discount
                raise ValidationError(_("入力された値は最小値(0)の制限より小さくなっています。: 値引率%"))
            if p.discount > 100:
                # self.discount = self._origin.discount
                raise ValidationError(_("入力された値は最大値(100)の制限より大きくなっています。: 値引率%"))

    def get_compute_lineamount(self, price_unit, discount, quantity):
        if price_unit is None:
            price_unit = 0
        if discount is None:
            discount = 0
        if quantity is None:
            quantity = 0
        result = price_unit * quantity - (discount * price_unit / 100) * quantity
        # TODO recounting rounding
        return round(result, 2)

    def get_compute_sale_unit_price(self, price_unit, discount):
        if price_unit is None:
            price_unit = 0
        if discount is None:
            discount = 0
        result = price_unit - discount * price_unit / 100
        # TODO recounting rounding
        return round(result, 2)

    def get_compute_discount_unit_price(self, price_unit, discount):
        if price_unit is None:
            price_unit = 0
        if discount is None:
            discount = 0
        result = - price_unit * discount / 100
        # TODO recounting rounding
        return round(result, 2)

    def _get_compute_line_tax_amount(self, line_amount, line_taxes, line_rounding, line_type):
        if line_amount != 0:
            return rounding(line_amount * line_taxes / 100, 2, line_rounding)
        else:
            return 0

    # def _get_computed_taxes(self):
    #     self.ensure_one()
    #     if self.product_id.taxes_id:
    #         tax_ids = self.product_id.taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
    #     else:
    #         tax_ids = False
    #     return tax_ids

    def compute_sale_unit_price(self):
        for line in self:
            line.invoice_custom_salesunitprice = self.get_compute_sale_unit_price(line.price_unit, line.discount)

    def compute_discount_unit_price(self):
        for line in self:
            line.invoice_custom_discountunitprice = self.get_compute_discount_unit_price(line.price_unit, line.discount)

    @api.depends('move_id.x_voucher_tax_transfer', 'move_id.customer_tax_rounding')
    def compute_line_amount(self):
        for line in self:
            line.invoice_custom_lineamount = self.get_compute_lineamount(line.price_unit, line.discount, line.quantity)

    @api.depends('move_id.x_voucher_tax_transfer', 'move_id.customer_tax_rounding',
                 'move_id.invoice_line_ids')
    def compute_line_tax_amount(self):
        for line in self:
            # line.price_unit = line._get_computed_price_unit()
            line.compute_line_amount()
            if (line.move_id.x_voucher_tax_transfer == 'foreign_tax'
                and line.product_id.product_tax_category != 'exempt') \
                    or (line.move_id.x_voucher_tax_transfer == 'custom_tax'
                        and line.product_id.product_tax_category == 'foreign'):
                line.line_tax_amount = self._get_compute_line_tax_amount(line.invoice_custom_lineamount,
                                                                         line.tax_rate,
                                                                         line.move_id.customer_tax_rounding,
                                                                         line.x_invoicelinetype)
            else:
                line.line_tax_amount = 0

    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids', 'x_invoicelinetype',
                  'move_id.x_voucher_tax_transfer', 'move_id.customer_tax_rounding', 'tax_rate')
    def _onchange_price_subtotal(self):
        for line in self:
            if line.exclude_from_invoice_tab == False:
                self._validate_price_unit()
                self._validate_discountrate()
            if line.x_invoicelinetype in ('通常', 'サンプル'):
                if line.quantity < 0:
                    line.quantity = line.quantity * (-1)
            else:
                if line.quantity > 0:
                    line.quantity = line.quantity * (-1)

            if not line.move_id.is_invoice(include_receipts=True):
                continue
            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())

            line.invoice_custom_salesunitprice = self.get_compute_sale_unit_price(line.price_unit, line.discount)
            line.invoice_custom_discountunitprice = self.get_compute_discount_unit_price(line.price_unit, line.discount)
            line.invoice_custom_lineamount = self.get_compute_lineamount(line.price_unit, line.discount, line.quantity)

            if (line.move_id.x_voucher_tax_transfer == 'foreign_tax'
                and line.product_id.product_tax_category != 'exempt') \
                    or (line.move_id.x_voucher_tax_transfer == 'custom_tax'
                        and line.product_id.product_tax_category == 'foreign'):
                line.line_tax_amount = self._get_compute_line_tax_amount(line.invoice_custom_lineamount,
                                                                         line.tax_rate,
                                                                         line.move_id.customer_tax_rounding,
                                                                         line.x_invoicelinetype)
            else:
                line.line_tax_amount = 0
            line._onchange_price_unit()

    def _get_computed_freigth_category(self):
        self.ensure_one()
        if self.product_id:
            if self.product_id.product_custom_freight_category:
                return self.product_id.product_custom_freight_category
            else:
                return self.product_maker_name
        else:
            return False

    def _get_computed_stantdard_number(self):
        self.ensure_one()
        if self.product_id:
            if self.product_id.product_custom_standardnumber:
                return self.product_id.product_custom_standardnumber
            else:
                return self.invoice_custom_standardnumber
        else:
            return False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                line.name = ''
                line.product_name = ''
                line.product_standard_price = 0
                line.x_product_cost_price = 0
                line.account_id = ''
                line.product_uom_id = ''
                line.tax_rate = ''
                line.product_maker_name = ''
                line.invoice_custom_standardnumber = ''
                company = ''
                continue
            line.name = line._get_computed_name()
            line.product_name = line.product_id.name
            line.product_standard_price = line.product_id.standard_price
            line.x_product_cost_price = line.product_id.cost
            line.account_id = line._get_computed_account()

            line.product_uom_id = line.product_id.product_uom_custom
            line.tax_rate = line.product_id.product_tax_rate
            line.product_maker_name = line.product_id.product_maker_name
            line.invoice_custom_standardnumber = line._get_computed_stantdard_number()

            # Convert the unit price to the invoice's currency.
            company = line.move_id.company_id
            # line.price_unit = company.currency_id._convert(line.price_unit, line.move_id.currency_id, company,
            #                                                line.move_id.date)

            # todo set price follow product code
            # line.price_unit = line._get_computed_price_unit()

        # Comment for changing UOM, Category to Char
        # if len(self) == 1:
        #     return {'domain': {'product_uom_id': [('category_id', '=', self.product_uom_id.category_id.id)]}}

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        exchange_rate = 1
        if self.move_id.partner_id.customer_apply_rate == "customer":
            if self.move_id.partner_id.customer_rate and self.move_id.partner_id.customer_rate > 0:
                exchange_rate = self.move_id.partner_id.customer_rate / 100
        elif self.move_id.partner_id.customer_apply_rate == "category":
            if self.product_id.product_class_code_lv4 \
                    and self.product_id.product_class_code_lv4.product_class_rate \
                    and self.product_id.product_class_code_lv4.product_class_rate > 0:
                exchange_rate = self.product_id.product_class_code_lv4.product_class_rate / 100

        if self.product_id.product_tax_category == 'exempt':
            self.price_no_tax = self.price_include_tax = self.price_unit / exchange_rate
        else:
            if self.move_id.x_voucher_tax_transfer == 'internal_tax':
                self.price_include_tax = self.price_unit / exchange_rate
                self.price_no_tax = self.price_unit / (self.tax_rate/100 + 1) / exchange_rate
            elif self.move_id.x_voucher_tax_transfer == 'custom_tax':
                if self.product_id.product_tax_category == 'foreign':
                    self.price_no_tax = self.price_unit / exchange_rate
                    self.price_include_tax = self.price_unit * (self.tax_rate / 100 + 1) / exchange_rate
                elif self.product_id.product_tax_category == 'internal':
                    self.price_include_tax = self.price_unit / exchange_rate
                    self.price_no_tax = self.price_unit / (self.tax_rate / 100 + 1) / exchange_rate
                else:
                    self.price_no_tax = self.price_include_tax = self.price_unit / exchange_rate
            else:
                self.price_no_tax = self.price_unit / exchange_rate
                self.price_include_tax = self.price_unit * (self.tax_rate / 100 + 1) / exchange_rate


    def _get_computed_price_unit(self):
        # Set price follow product code
        price_unit = 0
        if self.move_id.x_voucher_tax_transfer == 'internal_tax':
            price_unit = self.price_include_tax
        elif self.move_id.x_voucher_tax_transfer == 'custom_tax':
            if self.product_id.product_tax_category == 'foreign':
                price_unit = self.price_no_tax
            elif self.product_id.product_tax_category == 'internal':
                price_unit = self.price_include_tax
            else:
                price_unit = self.price_no_tax
        else:
            price_unit = self.price_no_tax

        if self.move_id.partner_id.customer_apply_rate == "customer":
            if self.move_id.partner_id.customer_rate and self.move_id.partner_id.customer_rate > 0:
                price_unit = price_unit * self.move_id.partner_id.customer_rate / 100
        elif self.move_id.partner_id.customer_apply_rate == "category":
            if self.product_id.product_class_code_lv4 \
                    and self.product_id.product_class_code_lv4.product_class_rate \
                    and self.product_id.product_class_code_lv4.product_class_rate > 0:
                price_unit = price_unit * self.product_id.product_class_code_lv4.product_class_rate / 100

        return rounding(price_unit, 0, self.move_id.customer_tax_rounding)

    @api.depends('move_id.x_voucher_tax_transfer')
    def compute_price_unit(self):
        for line in self:
            line.price_unit = line._get_computed_price_unit()

    def button_update(self):
        view = {
            'name': _('Invoice Lines'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': False,
            'create': True,
            'res_id': self.id,
        }
        return view


class ClassGetProductCode(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('show_product_code', True):
                product_code_1 = str(record.product_code_1)
                result.append((record.id, product_code_1))
        return result
