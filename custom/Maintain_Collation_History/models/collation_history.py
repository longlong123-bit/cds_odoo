# -*- coding: utf-8 -*-


from odoo import fields, models


class CollationPayment(models.Model):
    _inherit = 'bill.info'

    def _get_customer_other_cd(self):
        for cd in self:
            # if self.partner_id:
            cd.customer_other_cd = cd.partner_id.customer_other_cd

    # その他CD
    customer_other_cd = fields.Char('Customer CD', readonly=True, compute=_get_customer_other_cd)


class ClassBillInvoice(models.Model):
    _inherit = 'bill.invoice'


class ClassDetail(models.Model):
    _inherit = 'bill.invoice.details'

    def _get_product_default_code_detail(self):
        for default in self:
            if default.product_default_code:
                default.product_default_code = default.account_move_line_id.product_default_code

    product_default_code = fields.Char('Product Default Code', compute='_get_product_default_code_detail', readonly=True)

    def _get_partner_name_detail(self):
        for par in self:
            if par.account_move_line_id:
                par.partner_name = par.partner_id.name

    partner_name = fields.Char('Partner Name', compute='_get_partner_name_detail', readonly=True)

    def _get_product_custom_standerdnumber_detail(self):
        for cus in self:
            if cus.product_custom_standardnumber:
                cus.product_custom_standardnumber = cus.account_move_line_id.product_custom_standardnumber

    product_custom_standardnumber = fields.Char('Product Custom Standard Number',
                                                compute='_get_product_custom_standerdnumber_detail', readonly=True)

    def _get_product_maker_name_detail(self):
        for maker in self:
            if maker.product_maker_name:
                maker.product_maker_name = maker.account_move_line_id.product_maker_name

    product_maker_name = fields.Char('Product Maker Name', compute='_get_product_maker_name_detail', readonly=True)

    def _get_x_product_barcode(self):
        for maker in self:
            if maker.x_product_barcode:
                maker.x_product_barcode = maker.account_move_line_id.x_product_barcode

    x_product_barcode = fields.Char('Product Maker Name', compute='_get_x_product_barcode', readonly=True)

    def _get_x_product_name(self):
        for maker in self:
            if maker.x_product_name:
                maker.x_product_name = maker.account_move_line_id.x_product_name

    x_product_name = fields.Char('Product Maker Name', compute='_get_x_product_name', readonly=True)

    def _get_quantity(self):
        for maker in self:
            if maker.quantity:
                maker.quantity = maker.account_move_line_id.quantity

    quantity = fields.Float('Product Maker Name', compute='_get_quantity', readonly=True)

    def _get_price_unit_detail(self):
        for maker in self:
            if maker.price_unit:
                maker.price_unit = maker.account_move_line_id.price_unit
    price_unit = fields.Float(string='Unit Price', compute='_get_price_unit_detail', digits='Product Price')

    def _get_amount_residual(self):
        for maker in self:
            if maker.amount_residual:
                maker.amount_residual = maker.account_move_line_id.amount_residual

    amount_residual = fields.Char('Product Maker Name', compute='_get_amount_residual', readonly=True)

    def _get_tax_audit(self):
        for maker in self:
            if maker.tax_audit:
                maker.tax_audit = maker.account_move_line_id.tax_audit

    tax_audit = fields.Char('Product Maker Name', compute='_get_tax_audit', readonly=True)

    def _get_price_unit(self):
        for t in self:
            if t.tax:
                t.tax = t.account_move_line_id.tax_base_amount

    tax = fields.Float('Product Maker Name', compute='_get_price_unit', readonly=True)


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
            if default.product_default_code:
                default.product_default_code = default.product_id.default_code

    product_default_code = fields.Char('Product Default Code', compute='_get_product_default_code', readonly=True)

    def _get_product_custom_standerdnumber(self):
        for cus in self:
            if cus.product_custom_standardnumber:
                cus.product_custom_standardnumber = cus.product_id.product_custom_standardnumber

    product_custom_standardnumber = fields.Char('Product Custom Standard Number',
                                                compute='_get_product_custom_standerdnumber', readonly=True)

    def _get_product_maker_name(self):
        for maker in self:
            if maker.product_maker_name:
                maker.product_maker_name = maker.product_id.product_maker_name

    product_maker_name = fields.Char('Product Maker Name', compute='_get_product_maker_name', readonly=True)
