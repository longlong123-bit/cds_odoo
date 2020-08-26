# -*- coding: utf-8 -*-
from datetime import timedelta, time, datetime
import pytz
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
    _rec_name = "payment_date"
    _order = 'write_date desc'

    @api.model
    def get_default_journal(self):
        journal_id = self.env['account.journal']._search(
                [('type', '=', 'sale')], limit=1)
        return journal_id and journal_id[0] or False

    def get_default_payment_date(self):
        _date_now = datetime.now()
        return _date_now.astimezone(pytz.timezone(self.env.user.tz))

    name = fields.Char(string='新規', default='新規')
    many_payment_line_ids = fields.One2many('account.payment', 'many_payment_id', string='PaymentLine', copy=True,
                                            auto_join=True)
    payment_date = fields.Date(string='Transaction Date', default=get_default_payment_date)
    sales_rep = fields.Many2one('res.users', string='Sales Rep',
                                domain="[('share', '=', False)]", default=lambda self: self.env.user)
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', readonly=True, states={'draft': [('readonly', False)]}, default='outbound')
    state = fields.Selection(
        [('draft', 'Draft'), ('posted', 'Validated'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),
         ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    journal_id = fields.Many2one(
        string='vj_collection_method',
        comodel_name='account.journal',
        default=lambda self: self.get_default_journal())

    order_id = fields.Many2one('sale.order', string='Order', store=False)

    @api.onchange('history_payment')
    def _onchange_history_payment(self):
        if self.history_payment:
            results = []
            data = self.history_payment
            journal_id = self.env['account.journal']._search(
                [('type', '=', 'sale')], limit=1)
            if data:
                for line in data.bill_detail_ids:
                    results.append((0, 0, {
                        'partner_id': data.partner_id,
                        'partner_payment_name1': line.customer_name,
                        'payment_amount': line.line_amount + line.tax_amount,
                        'payment_method_id':
                        journal_id and journal_id[0] or False,
                        'vj_c_payment_category': 'cash'
                    }))

            self.many_payment_line_ids = results
