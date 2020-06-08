# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.test_convert.tests.test_env import record
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from lxml import etree
import simplejson

from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

ADDRESS_FIELDS = ('street', 'street2', 'address3', 'zip', 'city', 'state_id', 'country_id')


class CollationPayment(models.Model):
    # _name = 'collation.history'
    _inherit = 'account.move'

    line_ids = fields.One2many('account.move.line', 'move_id', string='Account Move Line')
    #

    # @api.depends('line_ids')
    # def _get_data_line_ids(self):
    #     for rec in self:
    #         rec.x_product_name = rec.line_ids.x_product_name
    #         rec.x_product_barcode = rec.line_ids.x_product_barcode

    # amount_untaxed_signed = fields.Monetary(string='Amount Untaxed Signed', readonly=True)
    # invoice_origin = fields.Char(string='Invoice Origin', default='0', readonly=True)
    # amount_total_signed = fields.Monetary(string='Amount Total Signed', default=1, readonly=True)
    # amount_tax = fields.Monetary(string='Amount Tax', default=1, readonly=True)
    # amount_total = fields.Monetary(string='Amount Total', default=1, readonly=True)
    # amount_residual = fields.Monetary(string="Amount Residual", default=1, readonly=True)
    # invoice_total_paid = fields.Monetary(string='Invoice Total Paid', readonly=True)
    # partner_id = fields.Many2one('res.partner', 'Res Partner')
    # product_id = fields.Many2many('product.product', string='Product', relation='acc_move_product',
    #                               column1='col_account_move_id', column2='col_product_id', default=1)

    # x_product_name = fields.Char(string='Product Name', relate='product_id.default_code')
    # @api.depends('product_id')

    # その他CD
    # customer_other_cd = fields.Char('Customer CD', readonly=True)

    # @api.depends('partner_id')
    def _get_res_partner_custom(self):
        for bill in self:
            # if rec.res_partner:
            bill.customer_code_bill = bill.partner_id.customer_code_bill
            # 請求先コード

    customer_code_bill = fields.Char(string='Billing Code', readonly=True, compute='_get_res_partner_custom')

    def _get_customer_other_cd(self):
        for cd in self:
            # if self.partner_id:
                cd.customer_other_cd = cd.partner_id.customer_other_cd

    # その他CD
    customer_other_cd = fields.Char('Customer CD', readonly=True, compute='_get_customer_other_cd')

    def _get_customer_bill_discount_rate(self):
        for rate in self:
            rate.customer_bill_discount_rate = rate.partner_id.customer_bill_discount_rate

    # 請求値引率
    customer_bill_discount_rate = fields.Char('Bill Discount Rate', readonly=True)

    x_history_voucher = fields.Many2one('account.move', string='Journal Entry',
                                        index=True, auto_join=True,
                                        help="The move of this entry line.")
    x_studio_price_list = fields.Integer(string='Price List')

    @api.depends('x_history_voucher')
    def _get_price_list(self):
        for price in self:
            price.x_studio_price_list = price.x_history_voucher.x_studio_price_list

    customer_closing_date = fields.Many2one('closing.date', 'Closing Date')


class ClassClosingDateCustom(models.Model):
    _name = 'closing.date'

    account_move_id = fields.One2many('account.move', 'partner_id')
    # commercial_partner_id


class ClassAccontMoveLineCustom(models.Model):
    _inherit = 'account.move.line'
    move_id = fields.Many2one('account.move', string='Account Move')

    def _get_partner_name(self):
        for par in self:
            if par.partner_id:
                par.partner_name = par.partner_id.name

    partner_name = fields.Char('Partner Name', compute='_get_partner_name', readonly=True)

    def _get_product_default_code(self):
        for default in self:
            default.product_default_code = default.product_id.default_code

    product_default_code = fields.Char('Product Default Code', compute='_get_product_default_code', readonly=True)

    def _get_product_custom_standerdnumber(self):
        for cus in self:
            cus.product_custom_standardnumber = cus.product_id.product_custom_standardnumber

    product_custom_standardnumber = fields.Char('Product Custom Standard Number',
                                                compute='_get_product_custom_standerdnumber', readonly=True)

    def _get_product_maker_name(self):
        for maker in self:
            maker.product_maker_name = maker.product_id.product_maker_name

    product_maker_name = fields.Char('Product Maker Name', compute='_get_product_maker_name', readonly=True)

    # def action_close_dialog(self):
    #     return {'type': 'ir.actions.act_window_close'}

    # @api.onchange
