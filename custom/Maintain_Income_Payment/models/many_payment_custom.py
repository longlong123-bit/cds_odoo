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
    payment_date = fields.Date(string='Transaction Date')
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

    history_payment = fields.Many2one('many.payment', string='History payment', store=False)


    @api.onchange('history_payment')
    def _onchange_order_id(self):
        self.set_order(self.history_payment.id)

    @api.model
    def set_order(self, history_payment):
        # TODO set history_payment
        data = self.env['product.product'].search([('id', '=', history_payment)])

        if data:
            self.payment_date = data.write_date

            # default = dict(None or [])
            # lines = [rec.copy_data()[0] for rec in data[0].many_payment_line_ids.sorted(key='id')]
            # print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # default['many_payment_line_ids'] = [(0, 0, line) for line in lines if line]
            # for rec in self:
            #     rec.many_payment_line_ids = default['many_payment_line_ids'] or ()
            # print("============================================================")
