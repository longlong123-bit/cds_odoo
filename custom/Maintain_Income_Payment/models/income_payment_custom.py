# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, time, datetime, date
import pytz
from addons.account.models.product import ProductTemplate
from odoo.tools.float_utils import float_round

import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import re
from odoo.osv import expression

from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.exceptions import ValidationError
import time
import calendar
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class IncomePaymentCustom(models.Model):
    _inherit = "account.payment"
    # _rec_name = 'document_no'
    _order = 'write_date desc'

    def get_default_payment_date(self):
        _date_now = datetime.now()
        return _date_now.astimezone(pytz.timezone(self.env.user.tz))

    customer_closing_date = fields.Date('Closing Date')
    closing_date_compute = fields.Integer('Temp')
    x_voucher_deadline = fields.Selection([('今回', '今回'), ('次回', '次回')])
    payment_terms = fields.Many2one('account.payment.term', 'Payment Terms', company_dependent=True, required=True,
                                    default=lambda self: self.env['account.payment.term'].search([('id', '=', 1)]))
    collection_method_date = fields.Integer(string='回収日', readonly=True, store=True)
    collection_method_month = fields.Integer(string='回収月', readonly=True, store=True)
    receivable = fields.Float(string='receivable')
    remain = fields.Float(string='remain')
    total_payment = fields.Float(string='total_payment')

    # set_read_only = fields.Boolean(string='', default=False, compute='_check_read_only')
    bill_status = fields.Char(string='bill_status')

    current_date = fields.Date(string='', default=get_default_payment_date, store=False)
    _defaults = {
        'current_date': lambda *a: time.strftime('%Y/%m/%d %H:%M:%S'),
    }
    partner_group_code = fields.Many2one('business.partner.group.custom', string='partner_group_code')
    customer_industry_code = fields.Many2one('res.partner.industry', string='Industry Code')
    is_customer_supplier_group_code = fields.Boolean(string='is_customer_supplier_group_code', default=False)
    is_industry_code = fields.Boolean(string='is_industry_code', default=False)
    customer_other_cd = fields.Char(string='Customer CD', store=True)
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')], default=False, help="Technical field for UX purpose.")
    many_code = fields.Char('Many_code')

    payment_id = fields.Many2one('account.payment', string="Originator Payment", copy=False,
                                 help="Payment that created this entry")
    many_payment_id = fields.Many2one('many.payment', string="Many payment", ondelete='cascade', index=True)
    # vj_c_payment_category = fields.Many2one('receipt.divide.custom', string='vj_c_payment_category', required=False)
    vj_c_payment_category = fields.Selection([
        ('cash', '現金'),
        ('bank', '銀行')], default='cash')

    payment_amount = fields.Float(string='Payment Amount')
    description = fields.Char(string='Description')
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', required=True, readonly=True, states={'draft': [('readonly', False)]}, default='inbound')

    def _get_default_client_id(self):
        return self.env['client.custom'].search([], limit=1, order='id').id

    client_custom_id = fields.Many2one('client.custom', default=_get_default_client_id, string='Client')

    def _get_latest_document_no(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'account.payment')])
        next = sequence.get_next_char(sequence.number_next_actual)
        return next

    document_no = fields.Char(string='Document No', default=_get_latest_document_no)
    company_id = fields.Many2one('res.company', 'Organization', default=lambda self: self.env.company.id, index=1)
    account_invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True,
                                         states={'draft': [('readonly', False)]})
    ari_document_no = fields.Char('ari_document_no')

    payment_date = fields.Date(string='Transaction Date', readonly=True, states={'draft': [('readonly', False)]})
    partner_bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account",
                                              states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one(string='Customer')
    partner_payment_name1 = fields.Char(string='paymentname1', readonly=True, states={'draft': [('readonly', False)]})
    partner_payment_name2 = fields.Char(string='paymentname2', readonly=True, states={'draft': [('readonly', False)]})
    partner_payment_address1 = fields.Char(string='Address 1', readonly=True, states={'draft': [('readonly', False)]})
    partner_payment_address2 = fields.Char(string='Address 2', readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one(string='Currency')
    sales_rep = fields.Many2one('res.users', string='Sales Rep', readonly=True, states={'draft': [('readonly', False)]},
                                domain="[('share', '=', False)]", default=lambda self: self.env.user)
    cb_partner_sales_rep_id = fields.Many2one('hr.employee', string='cbpartner_salesrep_id')
    comment_apply = fields.Text(string='commentapply', readonly=True, states={'draft': [('readonly', False)]})
    vj_summary = fields.Selection([('vj_sum_1', '専伝・仮伝'), ('vj_sum_2', '指定なし'), ('vj_sum_3', '通常')],
                                  string='vj_summary', readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one(string='vj_collection_method', default=lambda self: self.get_default_journal())

    state = fields.Selection(string='Document Status')

    account_payment_line_ids = fields.One2many('account.payment.line', 'payment_id', string='PaymentLine', copy=True)

    line_info = fields.Char(string='Line info', compute='_set_line_info')
    closing_date = fields.Date('closing_date')
    customer_from_date = fields.Date('From Date')

    invoice_history = fields.Many2one('account.move', string='Journal Entry', store=False)

    #TH - add dialog
    payment_input_history = fields.Many2one('account.payment', store=False)
    payment_request_history = fields.Many2one('bill.info', store=False)
    closing_date_new = fields.Char(string='Closing Date', readonly=True)
    payment_date_new = fields.Char(string='Payment Date', readonly=True)

    @api.onchange('partner_id')
    def onchange_payment_input_history(self):
        return {'domain': {'payment_input_history': [('partner_id', '=', self.partner_id.id)]}}

    @api.onchange('partner_id')
    def onchange_payment_request_history(self):
        return {'domain': {'payment_request_history': [('partner_id', '=', self.partner_id.id)]}}
    #TH - done

    @api.model
    def get_default_journal(self):
        journal_id = self.env['account.journal']._search(
                [('type', '=', 'sale')], limit=1)
        return journal_id and journal_id[0] or False

    @api.onchange('invoice_history')
    def _onchange_invoice_history(self):
        if self.invoice_history:
            results = []
            data = self.invoice_history
            self.partner_id = data.partner_id
            self.partner_payment_name1 = data.partner_id.name
            self.closing_date_new = data.partner_id.customer_closing_date.name
            self.payment_date_new = data.partner_id.customer_payment_date.name
            results.append((0, 0, {
                'payment_amount': data.amount_total
                # 'vj_c_payment_category': cash or ''
            }))

            self.account_payment_line_ids = results

    @api.onchange('partner_id', 'payment_terms', 'payment_term_custom_fix_month_day',
                  'payment_term_custom_fix_month_offset')
    def _get_date(self):
        for rec in self:
            for date in rec.partner_id.payment_terms:
                rec.collection_method_date = date.payment_term_custom_fix_month_day
                rec.collection_method_month = date.payment_term_custom_fix_month_offset

    check_onchange = 0

    @api.onchange('partner_id')
    def _get_detail_business_partner(self):
        # for rec in self:
        if self.partner_id:
            self._set_partner_info(self.partner_id)
            # self._set_partner_info()
            self.cb_partner_sales_rep_id = self.partner_id.customer_agent
            if self.check_onchange == 0:
                self.account_invoice_id = False
            else:
                self.check_onchange = 0

    @api.onchange('account_invoice_id')
    def _get_detail_business_partner_by_invoice(self):
        # for rec in self:
        self.check_onchange = 1
        if self.account_invoice_id:
            # self._set_partner_info()
            self._set_partner_info(self.account_invoice_id.partner_id)

    @api.onchange('account_payment_line_ids')
    def _get_detail_account_payment_line(self):
        self._set_line_info()
        # self._get_total_payment()

    @api.model
    def create(self, values):
        # if not ('document_no' in values):
        # get all document no. is number
        self._cr.execute('''
                        SELECT document_no
                        FROM account_payment
                        WHERE SUBSTRING(document_no, 5) ~ '^[0-9\.]+$';
                    ''')
        query_res = self._cr.fetchall()

        # generate new document no. by sequence
        seq = self.env['ir.sequence'].next_by_code('account.payment')
        # if new document no. already exits, do again
        while seq in [res[0] for res in query_res]:
            seq = self.env['ir.sequence'].next_by_code('account.payment')

        values['document_no'] = seq
        values['name'] = seq

        self._check_data(values)

        income_payment = super(IncomePaymentCustom, self).create(values)
        # self._check_amount()
        return income_payment

    # when change partner or invoice, reset other information of partner
    def _set_partner_info(self, values):
        for rec in self:
            rec.partner_id = values or ''
            rec.partner_payment_name1 = values.name or ''
            rec.closing_date_new = values.customer_closing_date.name or ''
            rec.payment_date_new = values.customer_payment_date.name or ''
            # TODO set name 4
            rec.partner_payment_name2 = values.customer_name_kana or ''
            rec.partner_payment_address1 = values.street or ''
            rec.partner_payment_address2 = values.street2 or ''
            rec.customer_other_cd = values.customer_other_cd or ''
            if values.customer_supplier_group_code:
                rec.is_customer_supplier_group_code = True
            if values.customer_industry_code:
                rec.is_industry_code = True

            self._set_line_info()

    # @api.constrains('partner_id')
    # def _pass_data_to_payment(self):
    #     if self.partner_id:
    #         results = []
    #         if self.payment_amount != 0:
    #             results.append((0, 0, {
    #                 'payment_amount': self.payment_amount,
    #                 'vj_c_payment_category': self.account_payment_line_ids.receipt_divide_custom_id.name or ''
    #             }))
    #
    #         self.account_payment_line_ids = results

    @api.constrains('partner_id')
    def _get_data_register(self):
        results = []
        if self.partner_id:
            for rec in self:
                values = rec.partner_id or ''
                rec.partner_payment_name1 = values.name or ''
                rec.closing_date_new = values.customer_closing_date.name or ''
                rec.payment_date_new = values.customer_payment_date.name or ''
                # TODO set name 4
                rec.partner_payment_name2 = values.customer_name_kana or ''
                rec.partner_payment_address1 = values.street or ''
                rec.partner_payment_address2 = values.street2 or ''
                rec.customer_other_cd = values.customer_other_cd or ''
                if values.customer_supplier_group_code:
                    rec.is_customer_supplier_group_code = True
                if values.customer_industry_code:
                    rec.is_industry_code = True

                # if self.amount != 0:
                #     results.append((0, 0, {
                #         'payment_amount': self.amount,
                #         'vj_c_payment_category': self.account_payment_line_ids.receipt_divide_custom_id.name
                #     }))
                #     self.account_payment_line_ids = results

                self._set_line_info()

    # set account amount info
    def _set_line_info(self):
        for rec in self:
            rec.line_info = ''
            total_payment_amounts = 0.00
            total_invoiced = 0.00

            amount_lines = rec.account_payment_line_ids.filtered(lambda line: line.payment_id)
            for line in amount_lines:
                total_payment_amounts += float(line.payment_amount)

            # ---- Count total_invoiced ----
            # set query
            query_res = False
            if rec.account_invoice_id:
                total_invoiced = rec.partner_id.total_invoiced or 0.00
                query = "SELECT amount_residual_signed " \
                        "FROM account_move " \
                        "WHERE state='posted' " \
                        "AND id=%s" % (rec.account_invoice_id.id)
                self._cr.execute(query)
                query_res = self._cr.fetchall()

                # update payment
                # query_update = "UPDATE account_payment " \
                #                "SET payment_amount=%s " \
                #                "WHERE account_invoice_id=%s " \
                #                "AND document_no=%s"
                # params_update = [total_payment_amounts, rec.account_invoice_id.id, rec.document_no]
                # self._cr.execute(query_update, params_update)

            elif rec.partner_id:
                query = "SELECT SUM(amount_residual_signed) " \
                        "FROM account_move " \
                        "WHERE state='posted' " \
                        "AND partner_id=%s " \
                        "GROUP BY partner_id" % (rec.partner_id.id)
                self._cr.execute(query)
                query_res = self._cr.fetchall()

                # update payment
                # query_update = "UPDATE account_payment " \
                #                "SET payment_amount=%s " \
                #                "WHERE partner_id=%s " \
                #                "AND document_no=%s " \
                #                "GROUP BY partner_id"
                # params_update = [total_payment_amounts, rec.partner_id.id, rec.document_no]
                # self._cr.execute(query_update, params_update)

            if query_res:
                total_invoiced = float([res[0] for res in query_res][0])

            receivable = (float(total_invoiced) - float(total_payment_amounts)) or 0.00
            if receivable < 0:
                receivable = 0

            rec.line_info = _('売掛残高：') + str("{:,.2f}".format(receivable)) + '　' \
                            + _('入金額合計：') + str("{:,.2f}".format(total_payment_amounts))

            if rec.account_payment_line_ids:
                query = "UPDATE account_payment " \
                        "SET payment_amount=%s,amount=%s" \
                        "WHERE document_no=%s "
                params = [total_payment_amounts, total_payment_amounts, rec.document_no]

                self._cr.execute(query, params)

    # tính ngày closing date dựa theo start day của payment
    @api.onchange('closing_date_compute', 'payment_date')
    def _get_closing_date(self):
        for rec in self:
            partner_id = self.partner_id
            account_move_related = self.account_invoice_id

            rec.closing_date_compute = partner_id.customer_closing_date.start_day
            if account_move_related.closing_date_compute:
                rec.x_voucher_deadline = account_move_related.x_voucher_deadline

            if rec.payment_date:
                day = int(rec.payment_date.strftime('%d'))
                closing_date = rec.closing_date_compute
                invoice_year = rec.payment_date.year
                invoice_month = rec.payment_date.month
                if int(day) > int(rec.closing_date_compute):
                    if rec.x_voucher_deadline == '今回':
                        try:
                            rec.customer_closing_date = date(invoice_year, invoice_month,
                                                             closing_date) + relativedelta(
                                months=1)
                        except ValueError:
                            cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                            rec.customer_closing_date = date(invoice_year, invoice_month,
                                                             cutoff_day) + relativedelta(
                                months=1)
                    else:
                        try:
                            rec.customer_closing_date = date(invoice_year, invoice_month,
                                                             closing_date) + relativedelta(
                                months=2)
                        except ValueError:
                            cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                            rec.customer_closing_date = date(invoice_year, invoice_month,
                                                             cutoff_day) + relativedelta(
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
                            rec.customer_closing_date = date(invoice_year, invoice_month,
                                                             closing_date) + relativedelta(
                                months=1)
                        except ValueError:
                            cutoff_day = calendar.monthrange(invoice_year, invoice_month)[1]
                            rec.customer_closing_date = date(invoice_year, invoice_month,
                                                             cutoff_day) + relativedelta(
                                months=1)


    # NGÀY KẾT SỔ
    def get_summary_date(self):
        for rec in self:
            if rec.account_invoice_id:
                query_date = "SELECT customer_closing_date, customer_from_date " \
                             "FROM account_move " \
                             "WHERE id=%s " % rec.account_invoice_id.id
            elif rec.partner_id:
                query_date = "SELECT customer_closing_date, customer_from_date " \
                             "FROM account_move " \
                             "WHERE partner_id=%s " \
                             "GROUP BY partner_id" % rec.partner_id.id

        self._cr.execute(query_date)
        query_res_date = self._cr.fetchall()
        customer_closing_date = [res[0] for res in query_res_date][0]
        customer_from_date = [res[1] for res in query_res_date][0]
        return customer_closing_date, customer_from_date

    # TỔNG TIỀN BÁN HÀNG THEO NGÀY KẾT SỔ
    def get_invoice_total(self):
        total_invoiced = 0.00
        get_date = self.get_summary_date()
        customer_closing_date = get_date[0]
        customer_from_date = get_date[0]
        for rec in self:
            if rec.document_no:
                total_invoiced = 0.00
                query_res = False
                if rec.account_invoice_id:
                    query = "SELECT SUM(amount_residual_signed) " \
                            "FROM account_move " \
                            "WHERE state='posted' " \
                            "AND id=%s " \
                            "AND customer_closing_date = %s"
                    # "AND customer_from_date > %s " \
                    # params = [rec.account_invoice_id.id, customer_from_date, customer_closing_date]
                    params = [rec.account_invoice_id.id, customer_closing_date]
                elif rec.partner_id:
                    query = "SELECT SUM(amount_residual_signed) " \
                            "FROM account_move " \
                            "WHERE state='posted' " \
                            "AND partner_id=%s " \
                            "AND customer_closing_date = %s " \
                            "GROUP BY partner_id"
                    params = [rec.partner_id.id, customer_closing_date, rec.partner_id.id]
                self._cr.execute(query, params)
                query_res = self._cr.fetchall()

            if query_res:
                total_invoiced = float([res[0] for res in query_res][0])

        return total_invoiced

    # TỔNG TIỀN NHẬP TIỀN THEO NGÀY KẾT SỔ
    def get_payment_total(self):
        total_payment_amounts = 0.00
        get_date = self.get_summary_date()
        customer_closing_date = get_date[0]
        customer_from_date = get_date[1]
        for rec in self:
            if rec.document_no:
                amount_lines = rec.account_payment_line_ids.filtered(lambda line: line.payment_id)
                for line in amount_lines:
                    total_payment_amounts += float(line.payment_amount)

                if rec.account_invoice_id:
                    account_invoice_id = rec.account_invoice_id.id
                    print('account_invoice_id')
                    print(account_invoice_id)
                    print('document_no')
                    print(rec.document_no)
                    query = "SELECT SUM(payment_amount)" \
                            "FROM account_payment " \
                            "WHERE account_invoice_id=%s " \
                            "AND state = 'posted' " \
                            "AND payment_date > %s " \
                            "AND payment_date < %s"
                    params = [rec.account_invoice_id.id, customer_from_date, customer_closing_date]

                elif rec.partner_id:
                    query = "SELECT SUM(payment_amount)" \
                            "FROM account_payment " \
                            "WHERE partner_id=%s " \
                            "AND state = 'posted' " \
                            "AND payment_date > %s " \
                            "AND payment_date < %s " \
                            "GROUP BY partner_id"
                    params = [rec.partner_id.id, customer_from_date, customer_closing_date]

            self._cr.execute(query, params)

        return total_payment_amounts

    # @api.constrains('document_no')
    def _check_amount(self):
        remain_amount = 0.00
        total_amount_payment = self.get_payment_total()
        total_amount_invoiced = self.get_invoice_total()
        remain_amount = total_amount_invoiced - total_amount_payment

    # Check validate, duplicate data
    def _check_data(self, values):
        # check document no.
        if values.get('document_no'):
            account_payment_count = self.env['account.payment'].search_count(
                [('document_no', '=', values.get('document_no'))])
            if account_payment_count > 0:
                raise ValidationError(_('The Document No has already been registered'))

        return True

    # Check payment_amount
    # @api.constrains('payment_amount')
    # def _check_payment_amount(self):
    #     for line in self:
    #         if line.payment_amount < 0:
    #             raise ValidationError(_('payment_amount must be more than 0'))

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        odoo/models.py
        """
        ctx = self._context.copy()
        if ctx.get('have_advance_search'):
            domain = []
            check = 0
            for se in args:
                if se[0] =='&':
                    continue
                if se[0] == 'search_category' and se[2] == 'equal':
                    check = 1
                if check == 1 and se[0] in ["partner_payment_name1", "sales_rep"]:
                    se[1] = '=ilike'
                if se[0] != 'search_category':
                    domain += [se]
                if se[0] == 'document_no':
                    string_middle = ''
                    for i in range(7 - len(se[2])):
                        string_middle += '0'
                    if len(se[2]) < 11:
                        se[2] = ''.join(["ARR-", string_middle, se[2]])
            args = domain
        res = super(IncomePaymentCustom, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res

class IncomePaymentLineCustom(models.Model):
    _name = "account.payment.line"

    payment_id = fields.Many2one('account.payment', string="Originator Payment", copy=False,
                                 help="Payment that created this entry")
    # vj_c_payment_category = fields.Many2one('receipt.divide.custom', string='vj_c_payment_category', required=False)
    vj_c_payment_category = fields.Selection([
        ('cash', '現金'),
        ('bank', '銀行')])
    payment_amount = fields.Float(string='Payment Amount')
    description = fields.Char(string='Description')
    name = fields.Char(string='Name')
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')], default=False, help="Technical field for UX purpose.")
    state = fields.Selection(
        [('draft', 'Draft'), ('posted', 'Validated'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),
         ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    payment_date = fields.Date(string='Transaction Date', readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one(string='Business Partner')
    partner_payment_name1 = fields.Char(string='paymentname1', readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', 'Organization', default=lambda self: self.env.company.id, index=1)
    journal_id = fields.Many2one(
        string='vj_collection_method',
        comodel_name='account.journal',
        default=lambda self: self.get_default_journal())
    receipt_divide_custom_id = fields.Many2one('receipt.divide.custom', string='Receipt Divide')
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', required=False)
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', required=True, readonly=True, states={'draft': [('readonly', False)]}, default='inbound')

    @api.model
    def get_default_journal(self):
        journal_id = self.env['account.journal']._search(
                [('type', '=', 'sale')], limit=1)
        return journal_id and journal_id[0] or False

    # Check payment_amount
    # @api.constrains('payment_amount')
    # def _check_payment_amount(self):
    #     for line in self:
    #         if line.payment_amount < 0:
    #             raise ValidationError(_('payment_amount must be more than 0'))

    def _compute_data_payment_line(self):
        for record in self:
            record.payment_date = record.payment_id.payment_date
            record.payment_date_display = record.payment_id.payment_date
            record.document_no = record.payment_id.document_no
            record.document_no_display = record.payment_id.document_no
            record.customer_other_cd = record.payment_id.customer_other_cd
            record.customer_other_cd_display = record.payment_id.customer_other_cd
            record.customer_code = record.payment_id.partner_id.customer_code
            record.customer_code_display = record.payment_id.partner_id.customer_code
            record.customer_name = record.payment_id.partner_payment_name1
            record.customer_name_display = record.payment_id.partner_payment_name1
            record.vj_c_payment_category = record.receipt_divide_custom_id.name
            record.vj_c_payment_category_display = record.receipt_divide_custom_id.name
            record.sales_rep = record.payment_id.sales_rep
            record.sales_rep_display = record.payment_id.sales_rep

    payment_date = fields.Date(store=True, compute=_compute_data_payment_line)
    document_no = fields.Char(store=True, compute=_compute_data_payment_line)
    customer_code = fields.Char(store=True, compute=_compute_data_payment_line)
    customer_name = fields.Char(store=True, compute=_compute_data_payment_line)
    customer_other_cd = fields.Char(store=True, compute=_compute_data_payment_line)
    vj_c_payment_category = fields.Char(store=True, compute=_compute_data_payment_line)
    sales_rep = fields.Char(store=True, compute=_compute_data_payment_line)
    payment_date_display = fields.Date(string="Payment Date", store=False, compute=_compute_data_payment_line)
    document_no_display = fields.Char(string="Document No", store=False, compute=_compute_data_payment_line)
    customer_code_display = fields.Char(string="Customer Code", store=False, compute=_compute_data_payment_line)
    customer_name_display = fields.Char(string="Customer Name", store=False, compute=_compute_data_payment_line)
    customer_other_cd_display = fields.Char(string="Customer Other CD", store=False, compute=_compute_data_payment_line)
    vj_c_payment_category_display = fields.Char(string="vj_c_payment_category", store=False, compute=_compute_data_payment_line)
    sales_rep_display = fields.Char(string="Sales Rep", store=False, compute=_compute_data_payment_line)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context.copy()
        if ctx.get('have_advance_search'):
            domain = []
            check = 0
            for se in args:
                if se[0] == '&':
                    continue
                if se[0] == 'search_category' and se[2] == 'equal':
                    check = 1
                if check == 1 and se[0] in ["partner_payment_name1", "sales_rep"]:
                    se[1] = '=ilike'
                if se[0] != 'search_category':
                    domain += [se]
                if se[0] == 'payment_id.document_no':
                    string_middle = ''
                    for i in range(7 - len(se[2])):
                        string_middle += '0'
                    if len(se[2]) < 11:
                        se[2] = ''.join(["ARR-", string_middle, se[2]])
            args = domain
        res = super(IncomePaymentLineCustom, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res