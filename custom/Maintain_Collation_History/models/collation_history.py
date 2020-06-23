# -*- coding: utf-8 -*-


from odoo import fields, models


class CollationPayment(models.Model):
    _inherit = 'bill.info'

    def _get_customer_other_cd(self):
        for cd in self:
            # if self.partner_id:
            cd.customer_other_cd = cd.partner_id.customer_other_cd

    def get_detail(self):
        records = self.env['bill.invoice.details'].search([('bill_info_id', 'in', self._ids)]).read()

        return {
            'template': 'bill_info_line',
            'records': records
        }

    # その他CD
    customer_other_cd = fields.Char('Customer CD', readonly=True, compute=_get_customer_other_cd)

    bill_detail_ids = fields.One2many('bill.invoice.details', 'bill_info_id')


class ClassBillInvoice(models.Model):
    _inherit = 'bill.invoice'


class ClassDetail(models.Model):
    _inherit = 'bill.invoice.details'

    jan_code = fields.Char('Product Code', compute='_get_account_move_line_db', readonly=True)
    product_name = fields.Char('Product Code', compute='_get_account_move_line_db', readonly=True)
    product_custom_standardnumber = fields.Char('Product Custom Standard Number',
                                                compute='_get_account_move_line_db', readonly=True)
    product_default_code = fields.Char('Product Default Code', compute='_get_account_move_line_db',
                                       readonly=True)
    quantity = fields.Float('Product Maker Name', compute='_get_account_move_line_db', readonly=True)
    price_unit = fields.Float(string='Unit Price', compute='_get_account_move_line_db', digits='Product Price')
    tax_audit = fields.Char('tax_audit', compute='_get_account_move_line_db', readonly=True)
    tax_amount = fields.Float('tax_amount', compute='_get_account_move_line_db', readonly=True)
    product_maker_name = fields.Char('Product Maker Name', compute='_get_account_move_line_db', readonly=True)
    line_amount = fields.Float('line amount', compute='_get_account_move_line_db', readonly=True)

    def _get_account_move_line_db(self):
        for acc in self:
            if acc.account_move_line_id:
                acc.jan_code = acc.account_move_line_id.x_product_barcode
                acc.product_name = acc.account_move_line_id.x_product_name
                acc.product_custom_standardnumber = acc.account_move_line_id.invoice_custom_standardnumber
                acc.product_default_code = acc.account_move_line_id.product_id.id
                acc.quantity = acc.account_move_line_id.quantity
                acc.price_unit = acc.account_move_line_id.price_unit
                acc.tax_audit = acc.account_move_line_id.tax_audit
                acc.tax_amount = acc.account_move_line_id.line_tax_amount
                acc.product_maker_name = acc.account_move_line_id.invoice_custom_FreightCategory
                acc.line_amount = acc.account_move_line_id.invoice_custom_lineamount


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
