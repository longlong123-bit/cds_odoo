# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ClassMasterPriceList(models.Model):
    _name = 'master.price.list'

    # Relational fields with another model
    maker_id = fields.Many2one('freight.category.custom', string="Maker Code")
    product_id = fields.Many2one('product.product', string="Product Id")

    # メーカーCD
    maker_code = fields.Char(string="Maker Code")

    # メーカー名
    maker_name = fields.Char(string="Maker Name")

    # 商品大分類CD
    product_class_code_lv1 = fields.Many2one('product.class', string="Main Category Code")

    # 大分類名
    product_class_name_lv1 = fields.Char(string="Main Category Name")

    # 商品中分類CD
    product_class_code_lv2 = fields.Many2one('product.class', string="Middle Category Code")

    # 中分類名
    product_class_name_lv2 = fields.Char(string="Middle Category Name")

    # 商品中小分類CD
    product_class_code_lv3 = fields.Many2one('product.class', string="Middle Small Category Code")

    # 中小分類名
    product_class_name_lv3 = fields.Char(string="Middle Small Category Name")

    # 商品小分類CD
    product_class_code_lv4 = fields.Many2one('product.class', string="Small Category Code")

    # 小分類名
    product_class_name_lv4 = fields.Char(string="Small Category Name")

    # JANコード
    jan_code = fields.Many2one('product.product', string="JAN Code")

    # 商品コード
    product_code = fields.Many2one('product.product', string="Product Code")

    # 品番 / 型番
    standard_number = fields.Many2one('product.product', string="Standard Number")

    # 商品名
    product_name = fields.Char(string="Product Name")

    # 地区コード
    country_state_code = fields.Many2one('res.country.state', string="Country State Code")

    # 地区名
    country_state_name = fields.Char(string="Country State Name")

    # 業種コード
    industry_code = fields.Many2one('res.partner.industry', string="Industry Code")

    # 業種名
    industry_name = fields.Char(string="Industry Name")

    # 取引先グループコード
    supplier_group_code = fields.Many2one('business.partner.group.custom', string="Supplier Group Code")

    # 取引先グループ名
    supplier_group_name = fields.Char(string="Supplier Group Name")

    # 請求先コード
    customer_code_bill = fields.Many2one('res.partner', string="Customer Code Bill")

    # 請求先名
    customer_name_bill = fields.Char(string="Customer Name Bill")

    # 得意先コード
    customer_code = fields.Many2one('res.partner', string="Customer Code")

    # 得意先名
    customer_name = fields.Char(string="Customer Name")

    # 採用価格
    recruitment_price = fields.Many2one('product.product', sting="Recruitment Price")

    # 掛率
    rate = fields.Float(string="Rate")

    # 適用売価
    price_applied = fields.Float(string="Price Applied")

    # 適用年月日
    date_applied = fields.Date(string="Date Applied")

    # Listen event onchange maker_code (メーカーCD)
    @api.onchange('maker_id')
    def _onchange_maker(self):
        if self.maker_id:
            self.maker_code = self.maker_id.search_key_freight
            self.maker_name = self.maker_id.name
        else:
            self.maker_code = self.maker_name = ''

    # Listen event onchange product_class_code_lv1
    @api.onchange('product_class_code_lv1')
    def _onchange_product_class_code_lv1(self):
        if self.product_class_code_lv1:
            # Set value for product_class_name_lv1 fields
            self.product_class_name_lv1 = self.product_class_code_lv1.name

            # Reset value for the lower-grade product
            self.product_class_code_lv2 = False
            self.product_class_code_lv3 = False
            self.product_class_code_lv4 = False

            # Set domain for product_class_code_lv2 fields
            _children_product_class_id = self.env['product.class'].search([
                ('product_parent_code.product_class_code', '=', self.product_class_code_lv1.product_class_code),
                ('id', '!=', self.product_class_code_lv1.id)
            ])
            _class_list = _children_product_class_id.ids
            domain = {'product_class_code_lv2': [('id', '=', _class_list)]}
            return {'domain': domain}
        else:
            self.product_class_name_lv1 = ''

    # Listen event onchange product_class_code_lv2
    @api.onchange('product_class_code_lv2')
    def _onchange_product_class_code_lv2(self):
        if self.product_class_code_lv2:
            # Set value for product_class_name_lv2 fields
            self.product_class_name_lv2 = self.product_class_code_lv2.name

            # Reset value for the lower-grade product
            self.product_class_code_lv3 = False
            self.product_class_code_lv4 = False

            # Set domain for product_class_code_lv3 fields
            children_product_class_id = self.env['product.class'].search([
                ('product_parent_code.product_class_code', '=', self.product_class_code_lv2.product_class_code),
                ('id', '!=', self.product_class_code_lv2.id)
            ])
            class_list = children_product_class_id.ids
            domain = {'product_class_code_lv3': [('id', '=', class_list)]}
            return {'domain': domain}
        else:
            self.product_class_name_lv2 = ''

    # Listen event onchange product_class_code_lv3
    @api.onchange('product_class_code_lv3')
    def _onchange_product_class_code_lv3(self):
        if self.product_class_code_lv3:
            # Set value for product_class_name_lv3 fields
            self.product_class_name_lv3 = self.product_class_code_lv3.name

            # Reset value for the lower-grade product
            self.product_class_code_lv4 = False

            # Set domain for product_class_code_lv4 fields
            children_product_class_id = self.env['product.class'].search([
                ('product_parent_code.product_class_code', '=', self.product_class_code_lv3.product_class_code),
                ('id', '!=', self.product_class_code_lv2.id)
            ])
            class_list = children_product_class_id.ids
            domain = {'product_class_code_lv4': [('id', '=', class_list)]}
            return {'domain': domain}
        else:
            self.product_class_name_lv3 = ''

    # Listen event onchange product_class_code_lv4
    @api.onchange('product_class_code_lv4')
    def _onchange_product_class_code_lv4(self):
        if self.product_class_code_lv4:
            # Set value for product_class_name_lv4 fields
            self.product_class_name_lv4 = self.product_class_code_lv4.name
        else:
            self.product_class_name_lv4 = ''

    # Listen event onchange jan_code （JANコード）
    @api.onchange('jan_code')
    def _onchange_jan_code(self):
        print("_onchange_jan_code")

    # Listen event onchange product_code （商品コード）
    @api.onchange('product_code')
    def _onchange_product_code(self):
        print("product_code")

    # Listen event onchange standard_number （品番 / 型番）
    @api.onchange('standard_number')
    def _onchange_standard_number(self):
        print("standard_number")

    # Listen event onchange country_state_code（地区コード）
    @api.onchange('country_state_code')
    def _onchange_country_state_code(self):
        if self.country_state_code:
            self.country_state_name = self.country_state_code.name
        else:
            self.country_state_name = ''

    # Listen event onchange industry_code（業種コード）
    @api.onchange('industry_code')
    def _onchange_industry_code(self):
        if self.industry_code:
            self.industry_name = self.industry_code.name
        else:
            self.industry_name = ''

    # Listen event onchange supplier_group_code（取引先グループコード）
    @api.onchange('supplier_group_code')
    def _onchange_supplier_group_code(self):
        if self.supplier_group_code:
            self.supplier_group_name = self.supplier_group_code.name
        else:
            self.supplier_group_name = ''

    # Listen event onchange customer_code_bill（請求先コード）
    @api.onchange('customer_code_bill')
    def _onchange_customer_code_bill(self):
        if self.customer_code_bill:
            self.customer_name_bill = self.customer_code_bill.name
        else:
            self.customer_name_bill = ''

    # Listen event onchange customer_code（得意先コード）
    @api.onchange('customer_code')
    def _onchange_customer_code(self):
        if self.customer_code:
            self.customer_name = self.customer_code.name
        else:
            self.customer_name = ''

    # Listen event onchange recruitment_price（採用価格）
    @api.onchange('recruitment_price')
    def _onchange_recruitment_price(self):
        print("_onchange_recruitment_price")
