# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, time, datetime
from addons.account.models.product import ProductTemplate
from odoo.tools.float_utils import float_round

import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import re
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class IncomePaymentCustom(models.Model):
    _inherit = "account.payment"
    _rec_name = 'document_no'
    _order = 'document_no'

    payment_terms = fields.Many2one('account.payment.term', 'Payment Terms', company_dependent=True, required=True,
                                    default=lambda self: self.env['account.payment.term'].search([('id', '=', 1)]))
    collection_method_date = fields.Integer(string='回収日', readonly=True, store=True)
    collection_method_month = fields.Integer(string='回収月', readonly=True, store=True)
    receivable = fields.Float(string='receivable')
    remain = fields.Float(string='remain')
    total_payment = fields.Float(string='total_payment')

    # set_read_only = fields.Boolean(string='', default=False, compute='_check_read_only')
    bill_status = fields.Many2one('account.move', string='')

    current_date = fields.Datetime(string='', default=datetime.now(), store=False)
    _defaults = {
        'current_date': lambda *a: time.strftime('%Y/%m/%d %H:%M:%S'),
    }
    partner_group_code = fields.Many2one('business.partner.group.custom', string='partner_group_code')
    customer_industry_code = fields.Many2one('res.partner.industry', string='Industry Code')
    is_customer_supplier_group_code = fields.Boolean(string='is_customer_supplier_group_code', default=False)
    is_industry_code = fields.Boolean(string='is_industry_code', default=False)
    customer_other_cd = fields.Char(string='Customer CD', store=True)
    write_date = fields.Date('Write Date')
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')], default=False, help="Technical field for UX purpose.")
    many_code = fields.Char('Many_code')

    payment_id = fields.Many2one('account.payment', string="Originator Payment", copy=False,
                                 help="Payment that created this entry")
    many_payment_id = fields.Many2one('many.payment', string="Many payment", ondelete='cascade', required=True,
                                      index=True)
    vj_c_payment_category = fields.Many2one('receipt.divide.custom', string='vj_c_payment_category')
    payment_amount = fields.Float(string='Payment Amount')
    description = fields.Char(string='Description')
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', required=True, readonly=True, states={'draft': [('readonly', False)]}, default='inbound')

    def _get_default_client_id(self):
        return self.env['client.custom'].search([], limit=1, order='id').id

    client_custom_id = fields.Many2one('client.custom', default=_get_default_client_id, string='Client')

    document_no = fields.Char(string='Document No')
    company_id = fields.Many2one('res.company', 'Organization', default=lambda self: self.env.company.id, index=1)
    account_invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True,
                                         states={'draft': [('readonly', False)]})
    ari_document_no = fields.Char('ari_document_no')

    payment_date = fields.Date(string='Transaction Date', readonly=True, states={'draft': [('readonly', False)]})
    partner_bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account",
                                              states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one(string='Business Partner')
    partner_payment_name1 = fields.Char(string='paymentname1', readonly=True, states={'draft': [('readonly', False)]})
    partner_payment_name2 = fields.Char(string='paymentname2', readonly=True, states={'draft': [('readonly', False)]})
    partner_payment_address1 = fields.Char(string='Address 1', readonly=True, states={'draft': [('readonly', False)]})
    partner_payment_address2 = fields.Char(string='Address 2', readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one(string='Currency')
    sales_rep = fields.Many2one('res.users', string='Sales Rep', readonly=True, states={'draft': [('readonly', False)]},
                                domain="[('share', '=', False)]", default=lambda self: self.env.user)
    cb_partner_sales_rep_id = fields.Many2one('res.partner', string='cbpartner_salesrep_id', tracking=True,
                                              readonly=True,
                                              states={'draft': [('readonly', False)]},
                                              domain="['|', ('company_id', '=', False), "
                                                     "('company_id', '=', company_id)]")
    comment_apply = fields.Text(string='commentapply', readonly=True, states={'draft': [('readonly', False)]})
    vj_summary = fields.Selection([('vj_sum_1', '専伝・仮伝'), ('vj_sum_2', '指定なし'), ('vj_sum_3', '通常')],
                                  string='vj_summary', readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one(string='vj_collection_method', default=1)

    state = fields.Selection(string='Document Status')

    account_payment_line_ids = fields.One2many('account.payment.line', 'payment_id', string='PaymentLine', copy=True)

    line_info = fields.Char(string='Line info', compute='_set_line_info')

    @api.onchange('partner_id', 'payment_terms', 'payment_term_custom_fix_month_day', 'payment_term_custom_fix_month_offset')
    def _get_date(self):
        for rec in self:
            for date in rec.partner_id.payment_terms:
                rec.collection_method_date = date.payment_term_custom_fix_month_day
                rec.collection_method_month = date.payment_term_custom_fix_month_offset

    @api.onchange('partner_id')
    def _get_detail_business_partner(self):
        # for rec in self:
        if self.partner_id:
            self._set_partner_info(self.partner_id)

    @api.onchange('account_invoice_id')
    def _get_detail_business_partner_by_invoice(self):
        # for rec in self:
        if self.account_invoice_id:
            self._set_partner_info(self.account_invoice_id.partner_id)

    @api.onchange('account_payment_line_ids')
    def _get_detail_account_payment_line(self):
        self._set_line_info()

    @api.model
    def create(self, values):
        if not ('document_no' in values):
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
        # self._update_amount()
        income_payment = super(IncomePaymentCustom, self).create(values)

        return income_payment

    # when change partner or invoice, reset other information of partner
    def _set_partner_info(self, values):
        for rec in self:
            rec.partner_id = values or ''
            rec.partner_payment_name1 = values.name or ''
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
            elif rec.partner_id:
                query = "SELECT SUM(amount_residual_signed) " \
                        "FROM account_move " \
                        "WHERE state='posted' " \
                        "AND partner_id=%s " \
                        "GROUP BY partner_id" % (rec.partner_id.id)
                self._cr.execute(query)
                query_res = self._cr.fetchall()

            if query_res:
                total_invoiced = float([res[0] for res in query_res][0])

            receivable = (float(total_invoiced) - float(total_payment_amounts)) or 0.00
            if receivable < 0:
                receivable = 0

            rec.line_info = _('売掛残高：') + str("{:,.2f}".format(receivable)) + '　' \
                            + _('入金額合計：') + str("{:,.2f}".format(total_payment_amounts))

            # if rec.document_no:
            #     if rec.account_invoice_id:
            #         account_invoice_id = rec.account_invoice_id.id
            #         print('11111111111111111111111111111111111111111111111')
            #         print(account_invoice_id)
            #         print('receivable')
            #         print(receivable)
            #         query_remain = "UPDATE account_payment  " \
            #                        "SET remain=%s " \
            #                        "WHERE account_invoice_id=%s"
            #         print(receivable)
            #         params = [receivable, account_invoice_id]
            #         print(receivable)
            #         self._cr.execute(query_remain, params)

            # TEST TEST TEST
            # query_received_remain = "SELECT remain " \
            #                         "FROM account_payment " \
            #                         "WHERE account_invoice_id=%s" % account_invoice_id
            # self._cr.execute(query_received_remain)
            # query_res_received_remain = self._cr.fetchall()
            # if query_res_received_remain:
            #     remain = float([res[0] for res in query_res_received_remain][0])
            # print('======================= UPDATE AMOUNT 2==================')
            # print('remain2')
            # print(remain)
            # query_update_amount = "UPDATE account_move " \
            #                       "SET amount_residual_signed=%s " \
            #                       ", amount_residual=%s " \
            #                       "WHERE id=%s  "
            # params = [remain, remain, account_invoice_id]
            # self._cr.execute(query_update_amount, params)
            # # update state payment
            # if remain == 0:
            #     query_update_state = "UPDATE account_move " \
            #                          " SET invoice_payment_state='paid' " \
            #                          " WHERE id=%s  " % account_invoice_id
            #     self._cr.execute(query_update_state)
            # print('========= co invoice_id ==========')

            # elif rec.partner_id:
            #     print('222222222222222222222222222222222222222')
            #     print(rec.partner_id.id)
            #     query_remain = "UPDATE account_payment  " \
            #                    "SET remain=%s " \
            #                    "WHERE partner_id=%s"
            #     params = [receivable, rec.partner_id.id]
            #     self._cr.execute(query_remain, params)

            # rec.remain = receivable
            # print('================= remain ================')
            # print(rec.remain)
            # total_payment = total_payment_amounts

    # def write(self, values):
    #     self._update_amount()
    #
    #     payment = super(IncomePaymentCustom, self).write(values)
    #
    #     return payment

    # UPDATE AMOUNT TO account_move
    # @api.constrains('document_no')
    # def _update_amount(self):
    #     for rec in self:
    #         if rec.document_no:
    #             remain = 0.00
    #             print('remain1')
    #             print(remain)
    #             query_res_received_remain = False
    #             if rec.account_invoice_id:
    #                 account_invoice_id = rec.account_invoice_id.id
    #                 print('account_invoice_id')
    #                 print(account_invoice_id)
    #                 query_received_remain = "SELECT remain " \
    #                                         "FROM account_payment " \
    #                                         "WHERE account_invoice_id=%s" % account_invoice_id
    #                 self._cr.execute(query_received_remain)
    #                 query_res_received_remain = self._cr.fetchall()
    #                 if query_res_received_remain:
    #                     remain = float([res[0] for res in query_res_received_remain][0])
    #                 print('======================= UPDATE AMOUNT 2==================')
    #                 print('remain2')
    #                 print(remain)
    #                 query_update_amount = "UPDATE account_move " \
    #                                       "SET amount_residual_signed=%s " \
    #                                       ", amount_residual=%s " \
    #                                       "WHERE id=%s  "
    #                 params = [remain, remain, account_invoice_id]
    #                 self._cr.execute(query_update_amount, params)
    #                 # update state payment
    #                 if remain == 0:
    #                     query_update_state = "UPDATE account_move " \
    #                                          " SET invoice_payment_state='paid' " \
    #                                          " WHERE id=%s  " % account_invoice_id
    #                     self._cr.execute(query_update_state)
    #                 print('========= co invoice_id ==========')
    # elif partner_id:
    #     # query_remain = "SELECT remain " \
    #     #                "FROM account_payment " \
    #     #                "WHERE id=%s" % partner_id
    #     # self._cr.execute(query_remain)
    #     # query_res_remain = self._cr.fetchall()
    #     # if query_res_remain:
    #     #     remain = float([res[0] for res in query_res_remain][0])
    #     print('======================= UPDATE AMOUNT 2==================')
    #     # print(remain)
    #     query_update_amount = "UPDATE account_move " \
    #                           "SET amount_residual_signed=%s " \
    #                           ", amount_residual=%s " \
    #                           "WHERE id=%s  "
    #     params = [rec.remain, rec.remain, partner_id]
    #     self._cr.execute(query_update_amount, params)
    #     if rec.remain == 0:
    #         query_update_state = "UPDATE account_move " \
    #                              " SET invoice_payment_state='paid' " \
    #                              " WHERE id=%s  " % partner_id
    #         self._cr.execute(query_update_state)
    #     print('========= ko co invoice_id ==========')
    # return True


    # Check validate, duplicate data
    def _check_data(self, values):
        # check document no.
        if values.get('document_no'):
            account_payment_count = self.env['account.payment'].search_count(
                [('document_no', '=', values.get('document_no'))])
            if account_payment_count > 0:
                raise ValidationError(_('The Document No has already been registered'))

        return True

    # check bill before delete
    # def unlink(self):
    #     print('------------------------------ DELETE -------------------------')
    #     print(self.partner_id)
    #     query_res = False
    #     for rec in self:
    #         if rec.partner_id:
    #             query = "SELECT partner_id " \
    #                     "FROM account_move " \
    #                     "WHERE bill_status = 'billed' " \
    #                     "AND id=%s" % rec.account_invoice_id.id
    #             self._cr.execute(query)
    #             query_res = self._cr.fetchall()
    #             print(query_res)
    #             if len(query_res) > 0:
    #                 raise ValidationError(_('Voucher is billed'))
    #             else:
    #                 print('------------------------------ PRINT -------------------------')
    #                 # total_invoiced = float([res[0] for res in query_res][0])
    #                 # print(total_invoiced)
    #                 return super(IncomePaymentCustom, self).unlink()

    # check readonly field
    # @api.constrains('document_no')
    # @api.constrains('account_invoice_id', 'document_no')
    # def _check_read_only(self):
    #     print('------------------------------ CHECK BILLED -------------------------')
    #     query_res = False
    #     for rec in self:
    #         query_res = False
    #         if rec.document_no:
    #             if rec.account_invoice_id:
    #                 query = "SELECT partner_id " \
    #                         "FROM account_move " \
    #                         "WHERE bill_status = 'billed' " \
    #                         "AND id=%s" % rec.account_invoice_id.id
    #                 self._cr.execute(query)
    #                 query_res = self._cr.fetchall()
    #                 print(query_res)
    #                 print(len(query_res))
    #                 if len(query_res) > 0:
    #                     rec.set_read_only = True
    #                 else:
    #                     rec.set_read_only = False
    #         rec.set_read_only = False


    # def button_history(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'product.product',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_id': self.id,
    #         'target': 'new',
    #     }


class IncomePaymentLineCustom(models.Model):
    _name = "account.payment.line"

    payment_id = fields.Many2one('account.payment', string="Originator Payment", copy=False,
                                 help="Payment that created this entry")
    vj_c_payment_category = fields.Many2one('receipt.divide.custom', string='vj_c_payment_category')
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
    journal_id = fields.Many2one(string='vj_collection_method', default=1)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', required=True, readonly=True,
                                        states={'draft': [('readonly', False)]}, default=1)
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', required=True, readonly=True, states={'draft': [('readonly', False)]}, default='inbound')
