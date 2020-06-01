# -*- coding: utf-8 -*-
from datetime import timedelta, time, datetime
from addons.account.models.product import ProductTemplate
from odoo.tools.float_utils import float_round

import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import re
from odoo.osv import expression


class PaymentTermCustom(models.Model):
    _inherit = "account.payment.term"
    # _rec_name = 'payment_term_custom_search_key'
    _order = 'payment_term_custom_search_key'

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id

    payment_term_custom_id = fields.Many2one('account.payment.term')

    payment_term_custom_client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)
    payment_term_company_id = fields.Many2one('res.company', 'Organization', default=lambda self: self.env.company.id, required=True,
                                              index=1)

    payment_term_custom_search_key = fields.Char(string="Search Key")
    note = fields.Char(string="Description")
    payment_term_custom_is_active = fields.Boolean(string="Active", default=True)
    payment_term_custom_is_default = fields.Boolean(string="Default")
    payment_term_custom_is_fixed_due_date = fields.Boolean(string="Fixed due date")
    payment_term_custom_is_after_delivery = fields.Boolean(string="After Delivery")
    payment_term_custom_is_next_business_day = fields.Boolean(string="Next Business Day")
    payment_term_custom_is_due_date_is_biz_day_only = fields.Boolean(string="Due Date is Biz Day only")
    payment_term_custom_is_next_biz_day_if_due_date_is_holiday = fields.Boolean(string="Next Biz Day if Due Date is Holiday")
    payment_term_custom_calendar = fields.Char(string="Calendar*")
    payment_term_custom_is_payment_terms = fields.Boolean(string="Payment Terms")
    payment_term_custom_fix_month_day = fields.Integer(string="Fix month day")
    payment_term_custom_fix_month_cutoff = fields.Integer(string="Fix month cutoff")
    payment_term_custom_fix_month_offset = fields.Integer(string="Fix month offset")
    payment_term_custom_discount_days = fields.Integer(string="Discount Days*")
    payment_term_custom_discount_percent = fields.Float(string="Discount %*")
    payment_term_custom_discount_days_2 = fields.Integer(string="Discount Days 2*")
    payment_term_custom_discount_2_percent = fields.Float(string="Discount 2 %*")
    payment_term_custom_grace_days = fields.Integer(string="Grace Days*")
    payment_term_custom_document_note = fields.Char(string="Document Note")
    payment_term_custom_payment_term_usage = fields.Char(string="Payment Term Usage*")
    payment_term_custom_ar_invoice_closing_date = fields.Date(string="AR Invoice Closing Date")
    payment_term_custom_ap_invoice_closing_date = fields.Date(string="AP Invoice Closing Date")
    payment_term_custom_is_valid = fields.Boolean(string="Valid")

    @api.model
    def create(self, values):
        if not (('payment_term_custom_search_key' in values) and values['payment_term_custom_search_key']):
            seq = self.env['ir.sequence'].next_by_code('account.payment.term')
            values['payment_term_custom_search_key'] = seq

        # self._check_data(values)

        payment_term = super(PaymentTermCustom, self).create(values)

        return payment_term

    # Check validate, duplicate data
    def _check_data(self, values):
        # check Search Key
        if values.get('payment_term_custom_search_key'):
            search_key_count = self.env['account.payment.term'].search_count(
                [('payment_term_custom_search_key', '=', values.get('payment_term_custom_search_key'))])
            if search_key_count > 0:
                raise ValidationError(_('The Search Key has already been registered'))

        return True

    def button_validate(self):
        # TODO
        print('------------Validate------------')
        return True