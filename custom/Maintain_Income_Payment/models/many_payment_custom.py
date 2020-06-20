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

    many_payment_line_ids = fields.One2many('account.payment', 'many_payment_id', string='PaymentLine', copy=True,
                                            auto_join=True)
    payment_date = fields.Date(string='Transaction Date', default=datetime.today())
    sales_rep = fields.Many2one('res.users', string='Sales Rep',
                                domain="[('share', '=', False)]", default=lambda self: self.env.user)
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', readonly=True, states={'draft': [('readonly', False)]}, default='outbound')
    state = fields.Selection(
        [('draft', 'Draft'), ('posted', 'Validated'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),
         ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    journal_id = fields.Many2one(string='vj_collection_method', default=1)

    order_id = fields.Many2one('sale.order', string='Order', store=False)

    history_payment = fields.Many2one('bill.info', string='History payment', store=False)

    @api.onchange('history_payment')
    def _onchange_history_payment(self):
        if self.history_payment:
            results = []
            data = self.env['bill.info'].search([('id', '=', self.history_payment.id)])

            for line in data.bill_detail_ids:
                results.append((0, 0, {
                    'partner_id': data.partner_id,
                    'partner_payment_name1': line.customer_name,
                    'payment_amount': line.line_amount + line.tax_amount,
                    'payment_method_id': 1,
                    'vj_c_payment_category': 1
                }))

            self.many_payment_line_ids = results
