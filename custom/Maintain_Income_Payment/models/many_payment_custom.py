# -*- coding: utf-8 -*-
from datetime import timedelta, time, datetime
from addons.account.models.product import ProductTemplate
from odoo.tools.float_utils import float_round

import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import re
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class ManyPaymentCustom(models.Model):

    _name = "many.payment"

    name = fields.Char(string='Name')
    payment_id = fields.Many2one('account.payment', string="Originator Payment", copy=False,
                                 help="Payment that created this entry")



    def _get_default_client_id(self):
        return self.env['client.custom'].search([], limit=1, order='id').id

    client_custom_id = fields.Many2one('client.custom', default=_get_default_client_id, string='Client')
    document_no = fields.Char(string='Document No')
    company_id = fields.Many2one('res.company', 'Organization', default=lambda self: self.env.company.id, index=1)
    account_invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True)
    #                                      states={'draft': [('readonly', False)]})

    many_payment_line_ids = fields.One2many('account.payment', 'many_payment_id', string='PaymentLine', copy=True)
    account_payment_line_ids = fields.One2many('account.payment.line', 'payment_id', string='PaymentLine', copy=True)
    line_info = fields.Char(string='Line info', compute='_set_line_info')
    partner_id = fields.Many2one(string='Business Partner')
    payment_date = fields.Date(string='Transaction Date')
    partner_payment_name1 = fields.Char(string='paymentname1', readonly=True)
    partner_payment_name2 = fields.Char(string='paymentname2', readonly=True)
    partner_payment_address1 = fields.Char(string='Address 1', readonly=True)
    partner_payment_address2 = fields.Char(string='Address 2', readonly=True)
    currency_id = fields.Many2one(string='Currency')
    sales_rep = fields.Many2one('res.users', string='Sales Rep',
                                domain="[('share', '=', False)]", default=lambda self: self.env.user)
    state = fields.Selection(
        [('draft', 'Draft'), ('posted', 'Validated'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),
         ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")

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
    # when change partner or invoice, reset other information of partner
    def _set_partner_info(self, values):
        for rec in self:
            rec.partner_id = values or ''
            rec.partner_payment_name1 = values.name or ''
            # TODO set name 4
            rec.partner_payment_name2 = values.customer_namef or ''
            rec.partner_payment_address1 = values.street or ''
            rec.partner_payment_address2 = values.street2 or ''

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


