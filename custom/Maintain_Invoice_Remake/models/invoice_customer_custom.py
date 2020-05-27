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


def rounding(number, pre=0, type_rounding='round'):
    """Rounding number by type rounding(round, roundup, rounddown)."""
    if number != 0:
        multiplier = 10 ** pre
        if type_rounding == 'roundup':
            return math.ceil(number * multiplier) / multiplier
        elif type_rounding == 'rounddown':
            return math.floor(number * multiplier) / multiplier
        else:
            return round(number, pre)
    else:
        return 0


class ClassInvoiceCustom(models.Model):
    _inherit = 'account.move'

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
        amount_untaxed_format = "${:,.2f}".format(self.amount_untaxed)
        amount_total_format = "${:,.2f}".format(self.amount_total)

        return str(len(self.invoice_line_ids)) + '明細 - (JPY)明細行合計:' + str(amount_untaxed_format) + ' / 総合計:' + str(
            amount_total_format) + ' = ' + str(amount_total_format)

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
    x_studio_business_partner = fields.Many2one('res.partner')
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
    x_studio_date_invoiced = fields.Date(string='Date Invoiced*', default=date.today())
    x_studio_date_printed = fields.Date(string='Date Printed', default=date.today())
    x_studio_date_shipment = fields.Date(string='Shipment Date*', default=date.today())
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
    x_voucher_tax_amount = fields.Monetary('消費税額')
    # x_voucher_deadline = fields.Selection([('今回', '次回','通常','来月勘定'), ('今回', '次回','通常','来月勘定')],default='今回')
    x_voucher_tax_transfer = fields.Selection([
        ('no_tax', '非課税'),
        ('foreign_tax', '外税／明細'),
        ('voucher', '伝票'),
        ('invoice', '請求'),
        ('internal_tax', '内税／明細'),
        ('custom_tax', '税調整別途')
    ], string='税転嫁', default='no_tax')

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
    customer_trans_classification_code = fields.Selection([('sale','掛売'),('cash','現金'), ('account','諸口')], string='Transaction Class')
    closing_date_compute = fields.Integer('Temp')

    x_voucher_deadline = fields.Selection([('今回', '今回'), ('次回', '次回')], default='今回')
    x_bussiness_partner_name_2 = fields.Char('名称2')
    x_studio_description = fields.Text('説明')
    x_userinput_id = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.uid)
    x_history_voucher = fields.Many2one('account.move', string='Journal Entry',
                                        index=True, auto_join=True,
                                        help="The move of this entry line.")
    sales_rep = fields.Many2one('res.users', string='Sales Rep', readonly=True, states={'draft': [('readonly', False)]},
                                domain="[('share', '=', False)]", default=lambda self: self.env.user)

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.x_invoicelinetype')
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
                        if (line.x_invoicelinetype != 'サンプル'):
                            if move.x_voucher_tax_transfer == 'voucher':
                                total_line_tax = sum(
                                    tax.amount for tax in line.tax_ids._origin.flatten_taxes_hierarchy())
                                line_tax_amount = (total_line_tax * line.price_unit * line.quantity) / 100
                                if line.x_invoicelinetype not in ('通常', 'サンプル', '消費税'):
                                    line_tax_amount = line_tax_amount * (-1)

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
            if move.x_voucher_tax_transfer == 'voucher':
                move.x_voucher_tax_amount = rounding(total_voucher_tax_amount, 2, move.customer_tax_rounding)
            else:
                move.x_voucher_tax_amount = total_voucher_tax_amount
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

    @api.onchange('x_history_voucher')
    def _onchange_x_test(self):
        result_l1 = []
        result_l2 = []
        for voucher in self:
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
            voucher.line_ids = []
            voucher.line_ids = result_l2
            voucher.invoice_line_ids = []
            voucher.invoice_line_ids = result_l1
            # voucher.x_history_voucher.invoice_line_ids

        self._set_tax_counting()
        self._onchange_invoice_line_ids()

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
            if rec.x_studio_business_partner:
                rec.partner_id = rec.x_studio_business_partner
                rec.x_studio_name = rec.x_studio_business_partner.name
                rec.x_studio_address_1 = rec.x_studio_business_partner.street
                rec.x_studio_address_2 = rec.x_studio_business_partner.street2
                rec.x_studio_address_3 = rec.x_studio_business_partner.address3
                rec.search_key = rec.x_studio_business_partner.search_key_partner
                rec.x_studio_sales_rep = rec.x_studio_business_partner.user_id
                rec.x_studio_payment_rule_1 = rec.x_studio_business_partner.payment_rule
                rec.x_studio_price_list = rec.x_studio_business_partner.property_product_pricelist
                rec.invoice_payment_terms_custom = rec.x_studio_business_partner.payment_terms
                rec.x_bussiness_partner_name_2 = rec.x_studio_business_partner.customer_name_kana
                rec.customer_tax_rounding = rec.x_studio_business_partner.customer_tax_rounding
                # Add customer info
                rec.customer_group = rec.x_studio_business_partner.customer_supplier_group_code.name
                rec.customer_state = rec.x_studio_business_partner.customer_state.name
                rec.customer_industry = rec.x_studio_business_partner.customer_industry_code.name
                rec.customer_trans_classification_code = rec.x_studio_business_partner.customer_trans_classification_code

                # set default 税転嫁 by 消費税区分 & 消費税計算区分
                customer_tax_category = rec.x_studio_business_partner.customer_tax_category
                customer_tax_unit = rec.x_studio_business_partner.customer_tax_unit

                # 消費税区分 = ３．非課税 or 消費税区分 is null or 消費税計算区分 is null ==> 税転嫁 = 非課税
                if (customer_tax_category == 'exempt') or (not customer_tax_category) or (not customer_tax_unit):
                    rec.x_voucher_tax_transfer = 'no_tax'
                else:
                    # 消費税計算区分 = １．明細単位
                    if customer_tax_unit == 'detail':
                        # 消費税区分 = １．外税 ==> 税転嫁 = 外税／明細
                        if customer_tax_category == 'foreign':
                            rec.x_voucher_tax_transfer = 'foreign_tax'
                        # 消費税区分 = 2．内税 ==> 税転嫁 = 内税／明細
                        else:
                            rec.x_voucher_tax_transfer = 'internal_tax'
                    # 消費税計算区分 = ２．伝票単位、３．請求単位 ==> 税転嫁 = 伝票、請求
                    else:
                        rec.x_voucher_tax_transfer = customer_tax_unit

                # call onchange of 税転嫁
                if rec.x_voucher_tax_transfer:
                    self._set_tax_counting()

    @api.onchange('x_voucher_tax_transfer')
    def _set_tax_counting(self):
        self._onchange_invoice_line_ids()
        for line in self.invoice_line_ids:
            line._onchange_product_id()
            line._onchange_price_subtotal()

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
        # for line in self.invoice_line_ids:
        #     line.compute_tax_ids()
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

    # tính ngày closing date dựa theo start day của customer
    @api.onchange('closing_date_compute', 'x_studio_date_invoiced', 'x_voucher_deadline', 'x_studio_business_partner')
    def _get_closing_date(self):
        for rec in self:
            rec.closing_date_compute = rec.x_studio_business_partner.customer_closing_date.start_day
            day = int(rec.x_studio_date_invoiced.strftime('%d'))
            closing_date = rec.closing_date_compute
            invoice_year = rec.x_studio_date_invoiced.year
            invoice_month = rec.x_studio_date_invoiced.month
            if int(day) > int(rec.closing_date_compute):
                if rec.x_voucher_deadline == '今回':
                    try:
                        rec.customer_closing_date = date(invoice_year, invoice_month, closing_date) + relativedelta(months=1)
                    except ValueError:
                        cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                        rec.customer_closing_date = date(invoice_year, invoice_month, cutoff_day) + relativedelta(months=1)
                else:
                    try:
                        rec.customer_closing_date = date(invoice_year, invoice_month, closing_date) + relativedelta(months=2)
                    except ValueError:
                        cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                        rec.customer_closing_date = date(invoice_year, invoice_month, cutoff_day) + relativedelta(months=2)
            else:
                if rec.x_voucher_deadline == '今回':
                    try:
                        rec.customer_closing_date = date(invoice_year, invoice_month, closing_date)
                    except ValueError:
                        cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                        rec.customer_closing_date = date(invoice_year, invoice_month, cutoff_day)

                else:
                    try:
                        rec.customer_closing_date = date(invoice_year, invoice_month, closing_date) + relativedelta(months=1)
                    except ValueError:
                        cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                        rec.customer_closing_date = date(invoice_year, invoice_month, cutoff_day) + relativedelta(months=1)

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
                tax_base_amount = line.invoice_custom_lineamount
                tax_amount = line.line_tax_amount

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
    def get_lines(self):
        records = self.env['account.move.line'].search([
            ('move_id', 'in', self._ids)
        ]).read()

        return {
            'template': 'invoice_lines',
            'records': records
        }

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
                line.x_product_barcode = detail_history.x_product_barcode
                line.x_product_modelnumber = detail_history.x_product_modelnumber
                line.x_product_name = detail_history.x_product_name
                line.x_product_name2 = detail_history.x_product_name2
                line.x_product_list_price = detail_history.x_product_list_price
                line.invoice_custom_standardnumber = detail_history.invoice_custom_standardnumber
                line.invoice_custom_uom_cost_value = detail_history.invoice_custom_uom_cost_value
                line.invoice_custom_discountunitprice = detail_history.invoice_custom_discountunitprice
                line.invoice_custom_discountrate = detail_history.invoice_custom_discountrate
                line.invoice_custom_lineamount = detail_history.invoice_custom_lineamount
                line.invoice_custom_Description = detail_history.invoice_custom_Description
                line.invoice_custom_salesunitprice = detail_history.invoice_custom_salesunitprice
                line.invoice_custom_FreightCategory = detail_history.invoice_custom_FreightCategory
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

    invoice_custom_line_no = fields.Integer('Line No', default=get_default_line_no)
    # Update 2020/04/28 - START
    x_invoicelinetype = fields.Selection([('通常', '通常'), ('返品', '返品'), ('値引', '値引'), ('サンプル', 'サンプル'), ('消費税', '消費税')],
                                         default='通常')
    x_product_barcode = fields.Many2one('product.product', string='JAN/UPC/EAN')
    x_product_barcode_show_in_tree = fields.Char(string='JANコード', related='x_product_barcode.barcode')
    x_product_code_show_in_tree = fields.Char(string='商品コード', related='x_product_barcode.product_code_1')

    x_product_modelnumber = fields.Char('Product')
    x_product_name = fields.Char('mproductname')
    x_product_name2 = fields.Char('mproductname2')
    x_product_list_price = fields.Float('List Price')
    # x_crm_purchased_products = fields.Many2one('crm.purchased_products', selection='generate_selection', string='Purchased products')

    # Update 2020/04/28 - END
    invoice_custom_standardnumber = fields.Char('standardnumber')
    invoice_custom_uom_cost_value = fields.Float('Cost Value')
    invoice_custom_discountunitprice = fields.Float('discountunitprice', compute='compute_discount_unit_price')
    invoice_custom_discountrate = fields.Float('discountrate')
    invoice_custom_salesunitprice = fields.Float('salesunitprice', compute='compute_sale_unit_price')
    invoice_custom_lineamount = fields.Float('Line Amount', compute='compute_line_amount')
    invoice_custom_Description = fields.Char('Description')
    invoice_custom_FreightCategory = fields.Many2one('freight.category.custom', string='FreightCategory')
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
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

    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount",
                               compute='compute_tax_ids')

    def compute_x_customer_show_in_tree(self):
        for line in self:
            line.x_customer_show_in_tree = line.move_id.x_studio_business_partner.name

    def compute_product_barcode_show_in_tree(self):
        for line in self:
            line.x_product_barcode_show_in_tree = line.x_product_barcode.barcode

    def compute_product_code_show_in_tree(self):
        for line in self:
            line.x_product_code_show_in_tree = line.x_product_barcode.product_code_1

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

    def compute_tax_ids(self):
        for line in self:
            line.tax_ids = line.product_id.taxes_id

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

    def compute_line_amount(self):
        for line in self:
            line.invoice_custom_lineamount = self.get_compute_lineamount(line.price_unit, line.discount, line.quantity)

    def compute_line_tax_amount(self):
        for line in self:
            if line.move_id.x_voucher_tax_transfer in ('foreign_tax', 'custom_tax'):
                total_line_tax = sum(tax.amount for tax in line.tax_ids._origin.flatten_taxes_hierarchy())
                line.line_tax_amount = self._get_compute_line_tax_amount(line.invoice_custom_lineamount,
                                                                         total_line_tax,
                                                                         line.move_id.customer_tax_rounding,
                                                                         line.x_invoicelinetype)
            else:
                line.line_tax_amount = 0

    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids', 'x_invoicelinetype')
    def _onchange_price_subtotal(self):
        for line in self:
            if line.exclude_from_invoice_tab == False:
                self._validate_price_unit()
                self._validate_discountrate()
            # print('test detail')
            # print(line.x_invoicelinetype)
            # print('end test')
            if line.x_invoicelinetype in ('通常', 'サンプル', '消費税'):
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

            if line.move_id.x_voucher_tax_transfer in ('foreign_tax', 'custom_tax'):
                total_line_tax = sum(tax.amount for tax in line.tax_ids._origin.flatten_taxes_hierarchy())
                line.line_tax_amount = self._get_compute_line_tax_amount(line.invoice_custom_lineamount,
                                                                         total_line_tax,
                                                                         line.move_id.customer_tax_rounding,
                                                                         line.x_invoicelinetype)
            else:
                line.line_tax_amount = 0

    def _get_computed_freigth_category(self):
        self.ensure_one()
        if self.product_id:
            if self.product_id.product_custom_freight_category:
                return self.product_id.product_custom_freight_category
            else:
                return self.invoice_custom_FreightCategory
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

    # def _get_computed_name(self):
    #     self.ensure_one()
    #
    #     if not self.product_id:
    #         return ''
    #
    #     if self.partner_id.lang:
    #         product = self.product_id.with_context(lang=self.partner_id.lang)
    #     else:
    #         product = self.product_id
    #
    #     values = []
    #     if product.partner_ref:
    #         values.append(product.partner_ref)
    #     if self.journal_id.type == 'sale':
    #         if product.description_sale:
    #             values.append(product.description_sale)
    #     elif self.journal_id.type == 'purchase':
    #         if product.description_purchase:
    #             values.append(product.description_purchase)
    #     return '\n'.join(values)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            line.name = line._get_computed_name()
            line.x_product_name = line.product_id.name

            # line.x_product_list_price = line.product_id.list_price
            # todo set price follow product code
            # line.x_product_list_price = line.product_id.price_no_tax_1

            # todo set price follow product code
            if line.move_id.x_voucher_tax_transfer == 'internal_tax':
                line.price_unit = line.product_id.price_include_tax_1
            else:
                line.price_unit = line.product_id.price_no_tax_1

            line.x_product_barcode = line.product_id
            line.account_id = line._get_computed_account()

            # line.tax_ids = line._get_computed_taxes()
            # line.tax_ids = line.product_id.taxes_id
            line.compute_tax_ids()

            line.product_uom_id = line._get_computed_uom()
            # line.price_unit = line._get_computed_price_unit()
            line.invoice_custom_FreightCategory = line._get_computed_freigth_category()
            line.invoice_custom_standardnumber = line._get_computed_stantdard_number()
            # Manage the fiscal position after that and adapt the price_unit.
            # E.g. mapping a price-included-tax to a price-excluded-tax must
            # remove the tax amount from the price_unit.
            # However, mapping a price-included tax to another price-included tax must preserve the balance but
            # adapt the price_unit to the new tax.
            # E.g. mapping a 10% price-included tax to a 20% price-included tax for a price_unit of 110 should preserve
            # 100 as balance but set 120 as price_unit.
            if line.tax_ids and line.move_id.fiscal_position_id:
                line.price_unit = line._get_price_total_and_subtotal()['price_subtotal']
                line.tax_ids = line.move_id.fiscal_position_id.map_tax(line.tax_ids._origin,
                                                                       partner=line.move_id.partner_id)
                accounting_vals = line._get_fields_onchange_subtotal(price_subtotal=line.price_unit,
                                                                     currency=line.move_id.company_currency_id)
                balance = accounting_vals['debit'] - accounting_vals['credit']
                line.price_unit = line._get_fields_onchange_balance(balance=balance).get('price_unit', line.price_unit)

            # Convert the unit price to the invoice's currency.
            company = line.move_id.company_id
            # line.price_unit = company.currency_id._convert(line.price_unit, line.move_id.currency_id, company,
            #                                                line.move_id.date)

        if len(self) == 1:
            return {'domain': {'product_uom_id': [('category_id', '=', self.product_uom_id.category_id.id)]}}

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
