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


class QuotationsCustom(models.Model):
    _inherit = "sale.order"
    # _rec_name = 'document_no'
    _order = 'document_no'

    name = fields.Char(string='Name', default=None)
    shipping_address = fields.Char(string='Shipping Address')
    expected_date = fields.Date(string='Expected Date')
    note = fields.Text(string='Note')
    create_date = fields.Datetime(string='Create Date')
    amount_untaxed = fields.Monetary(string='Amount Untaxed')
    amount_tax = fields.Monetary(string='Amount Tax')
    amount_total = fields.Monetary(string='Amount Total')
    partner_id = fields.Many2one(string='Partner Order')

    document_no = fields.Char(string='Document No')
    expiration_date = fields.Date(string='Expiration Date')
    comment = fields.Text(string='Comment')
    is_unit_quotations = fields.Boolean(string='Unit Quotations')
    is_print_date = fields.Boolean(string='Print Date')
    tax_method = fields.Selection([
            ('foreign_tax', '外税／明細'),
            ('slip', '伝票'),
            ('clam', '請求'),
            ('tax', '内税／明細'),
            ('custom_tax', '税調整別途')
            ], string='Tax Method')
    quotations_date = fields.Date(string='Quotations Date')
    order_id = fields.Many2one('sale.order', string='Order')
    partner_id = fields.Many2one(string='Business Partner')
    partner_name = fields.Char(string='Partner Name')
    sales_rep = fields.Many2one('res.users', string='Sales Rep', readonly=True, states={'draft': [('readonly', False)]},
                                domain="[('share', '=', False)]", default=lambda self: self.env.user)
    cb_partner_sales_rep_id = fields.Many2one('res.partner', string='cbpartner_salesrep_id', tracking=True,
                                              readonly=True,
                                              states={'draft': [('readonly', False)]},
                                              domain="['|', ('company_id', '=', False), "
                                                     "('company_id', '=', company_id)]")
    comment_apply = fields.Text(string='Comment Apply', readonly=True, states={'draft': [('readonly', False)]})
    report_header = fields.Selection([
        ('quotation', 'Quotation'),
        ('invoice', 'Invoice'),
        ('sale', 'Sale')
    ], string='Report Header', readonly=False, default='quotation')
    paperformat_id = fields.Many2one(related='company_id.paperformat_id', string='Paper Format')

    @api.onchange('partner_id')
    def _get_detail_product(self):
        if self.partner_id:
            for rec in self:
                rec.partner_id = self.partner_id or ''
                rec.partner_name = self.partner_id.name or ''

    @api.model
    def create(self, values):
        # if not ('document_no' in values):
        #     # get all document no. is number
        #     self._cr.execute('''
        #                     SELECT document_no
        #                     FROM account_payment
        #                     WHERE SUBSTRING(document_no, 5) ~ '^[0-9\.]+$';
        #                 ''')
        #     query_res = self._cr.fetchall()
        #
        #     # generate new document no. by sequence
        #     seq = self.env['ir.sequence'].next_by_code('account.payment')
        #     # if new document no. already exits, do again
        #     while seq in [res[0] for res in query_res]:
        #         seq = self.env['ir.sequence'].next_by_code('account.payment')
        #
        #     values['document_no'] = seq
        #     values['name'] = seq
        #
        # self._check_data(values)
        if 'report_header' in values:
            self.env.company.report_header = dict(self._fields['report_header'].selection).get(
                values.get('report_header'))

        quotations_custom = super(QuotationsCustom, self).create(values)

        return quotations_custom


class QuotationsLinesCustom(models.Model):
    _inherit = "sale.order.line"

    name = fields.Text(string='Description', default='New')
    tax_id = fields.Many2many(string='Taxes')
    product_id = fields.Many2one(string='Product')
    product_uom_qty = fields.Float(string='Product UOM Qty')
    product_uom = fields.Many2one(string='Product UOM')
    price_unit = fields.Float(string='Price Unit')

    class_item = fields.Selection([
        ('normal', 'Normal'),
        ('returns', 'Returns'),
        ('discount', 'Discount'),
        ('consumption_tax', 'Consumption Tax')
    ], string='Class Item')
    product_barcode = fields.Char(string='Product Barcode')
    product_freight_category = fields.Many2one('freight.category.custom', 'Freight Category')
    product_name = fields.Char(string='Product Name')
    product_standard_number = fields.Char(string='Product Standard Number')
    product_list_price = fields.Float(string='Product List Price')
    cost = fields.Float(string='Cost')
    # price_total = fields.Monetary(string='Total')
    description = fields.Text(string='Description')

    @api.onchange('product_id')
    def _get_detail_product(self):
        if self.product_id:
            for rec in self:
                rec.product_id = self.product_id or ''
                rec.product_barcode = self.product_id.barcode or ''
                rec.product_freight_category = self.product_id.product_custom_freight_category or ''
                rec.product_name = self.product_id.name or ''
                rec.product_list_price = self.product_id.list_price or ''
