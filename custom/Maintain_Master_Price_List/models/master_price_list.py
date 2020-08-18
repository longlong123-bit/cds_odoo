# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ClassMasterPriceList(models.Model):
    _name = 'master.price.list'

    # Relational fields with another model
    maker_id = fields.Many2one('freight.category.custom', string="Maker Code")
    product_id = fields.Many2one('product.product', string="Product Id")

    # メーカーCD
    maker_code = fields.Char(string="Maker Code", compute='compute_maker_code')

    # メーカー名
    maker_name = fields.Char('Maker Name')

    # 商品大分類CD
    product_class_code_lv1_id = fields.Many2one('product.class', string="Main Category Code")
    product_class_code_lv1 = fields.Char(string='Main Category Code', compute='compute_class_lv1')

    # 大分類名
    product_class_name_lv1 = fields.Char(string="Main Category Name", compute='compute_class_lv_all')

    # 商品中分類CD
    product_class_code_lv2_id = fields.Many2one('product.class', string="Middle Category Code")
    product_class_code_lv2 = fields.Char(string="Middle Category Code", compute='compute_class_lv2')

    # 中分類名
    product_class_name_lv2 = fields.Char(string="Middle Category Name", compute='compute_class_lv_all')

    # 商品中小分類CD
    product_class_code_lv3_id = fields.Many2one('product.class', string="Middle Small Category Code")
    product_class_code_lv3 = fields.Char(string="Middle Small Category Code", compute='compute_class_lv3')

    # 中小分類名
    product_class_name_lv3 = fields.Char(string="Middle Small Category Name", compute='compute_class_lv_all')

    # 商品小分類CD
    product_class_code_lv4_id = fields.Many2one('product.class', string="Small Category Code")
    product_class_code_lv4 = fields.Char(string="Small Category Code", compute='compute_class_lv4')

    # 小分類名
    product_class_name_lv4 = fields.Char(string="Small Category Name", compute='compute_class_lv_all')

    # JANコード
    jan_code_id = fields.Many2one('product.product', string="JAN Code")
    jan_code = fields.Char(string="JAN Code", compute='compute_jan_code')

    # 商品コード
    product_code_id = fields.Many2one('product.product', string="Product Code")
    product_code = fields.Char(string="Product Code", compute='compute_product_code')

    # 品番 / 型番
    standard_number_id = fields.Many2one('product.product', string="Standard Number")
    standard_number = fields.Char(string="Standard Number", compute='compute_standard_number')

    # 商品名
    product_name = fields.Char(string="Product Name", store=True)

    # 地区コード
    country_state_code_id = fields.Many2one('res.country.state', string="Country State Code", domain=[('country_id.code', '=', 'JP')])
    country_state_code = fields.Char(string="Country State Code", compute='compute_country_state_code')

    # 地区名
    country_state_name = fields.Char(string="Country State Name", store=True)

    # 業種コード
    industry_code_id = fields.Many2one('res.partner.industry', string="Industry Code")
    industry_code = fields.Char(string="Industry Code", compute='compute_industry_code')

    # 業種名
    industry_name = fields.Char(string="Industry Name", store=True)

    # 取引先グループコード
    supplier_group_code_id = fields.Many2one('business.partner.group.custom', string="Supplier Group Code")
    supplier_group_code = fields.Char(string="Supplier Group Code", compute='compute_supplier_group_code')

    # 取引先グループ名
    supplier_group_name = fields.Char(string="Supplier Group Name", store=True)

    # 請求先コード
    customer_code_bill_id = fields.Many2one('res.partner', string="Customer Code Bill")
    customer_code_bill = fields.Char(string="Customer Code Bill", compute='compute_customer_code_bill')

    # 請求先名
    customer_name_bill = fields.Char(string="Customer Name Bill", store=True)

    # 得意先コード
    customer_code_id = fields.Many2one('res.partner', string="Customer Code")
    customer_code = fields.Char(string="Customer Code", compute='compute_customer_code')

    # 得意先名
    customer_name = fields.Char(string="Customer Name", store=True)

    # 採用価格
    recruitment_price_id = fields.Many2one('product.product', sting="Recruitment Price")
    recruitment_price = fields.Char(sting="Recruitment Price", compute='compute_recruitment_price')

    # 掛率
    rate = fields.Float(string="Rate")

    # 適用売価
    price_applied = fields.Float(string="Price Applied")

    # 適用年月日
    date_applied = fields.Date(string="Date Applied")


    # Listen event onchange maker_code (メーカーCD)
    @api.onchange('maker_id')
    @api.constrains('maker_id')
    def _onchange_maker(self):
        for line in self:
            if line.maker_id:
                line.maker_name = line.maker_id.name
            else:
                line.maker_name = ''

    # Listen event onchange product_class_code_lv1
    @api.onchange('product_class_code_lv1_id')
    def _onchange_product_class_code_lv1(self):
        if self.product_class_code_lv1_id:
            # Set value for product_class_name_lv1 fields
            self.product_class_name_lv1 = self.product_class_code_lv1_id.name

            # Reset value for the lower-grade product
            self.product_class_code_lv2_id = False
            self.product_class_code_lv3_id = False
            self.product_class_code_lv4_id = False

            # Set domain for product_class_code_lv2 fields
            _children_product_class_id = self.env['product.class'].search([
                ('product_parent_code.product_class_code', '=', self.product_class_code_lv1_id.product_class_code),
                ('id', '!=', self.product_class_code_lv1_id.id)
            ])
            _class_list = _children_product_class_id.ids
            domain = {'product_class_code_lv2_id': [('id', '=', _class_list)]}
            return {'domain': domain}
        else:
            self.product_class_name_lv1 = ''

    # Listen event onchange product_class_code_lv2
    @api.onchange('product_class_code_lv2_id')
    def _onchange_product_class_code_lv2(self):
        if self.product_class_code_lv2_id:
            # Set value for product_class_name_lv2 fields
            self.product_class_name_lv2 = self.product_class_code_lv2_id.name

            # Reset value for the lower-grade product
            self.product_class_code_lv3_id = False
            self.product_class_code_lv4_id = False

            # Set domain for product_class_code_lv3 fields
            children_product_class_id = self.env['product.class'].search([
                ('product_parent_code.product_class_code', '=', self.product_class_code_lv2_id.product_class_code),
                ('id', '!=', self.product_class_code_lv2_id.id)
            ])
            class_list = children_product_class_id.ids
            domain = {'product_class_code_lv3_id': [('id', '=', class_list)]}
            return {'domain': domain}
        else:
            self.product_class_name_lv2 = ''

    # Listen event onchange product_class_code_lv3
    @api.onchange('product_class_code_lv3_id')
    def _onchange_product_class_code_lv3(self):
        if self.product_class_code_lv3_id:
            # Set value for product_class_name_lv3 fields
            self.product_class_name_lv3 = self.product_class_code_lv3_id.name

            # Reset value for the lower-grade product
            self.product_class_code_lv4_id = False

            # Set domain for product_class_code_lv4 fields
            children_product_class_id = self.env['product.class'].search([
                ('product_parent_code.product_class_code', '=', self.product_class_code_lv3_id.product_class_code),
                ('id', '!=', self.product_class_code_lv3_id.id)
            ])
            class_list = children_product_class_id.ids
            domain = {'product_class_code_lv4_id': [('id', '=', class_list)]}
            return {'domain': domain}
        else:
            self.product_class_name_lv3 = ''

    # Listen event onchange product_class_code_lv4
    @api.onchange('product_class_code_lv4_id')
    def _onchange_product_class_code_lv4(self):
        if self.product_class_code_lv4_id:
            # Set value for product_class_name_lv4 fields
            self.product_class_name_lv4 = self.product_class_code_lv4_id.name
        else:
            self.product_class_name_lv4 = ''

    # Listen event onchange jan_code （JANコード）
    @api.onchange('jan_code_id')
    @api.constrains('jan_code_id')
    def _onchange_jan_code(self):
        print("_onchange_jan_code")

    # Listen event onchange product_code （商品コード）
    @api.onchange('product_code_id')
    @api.constrains('product_code_id')
    def _onchange_product_code(self):
        print("product_code")

    # Listen event onchange standard_number （品番 / 型番）
    @api.onchange('standard_number_id')
    @api.constrains('standard_number_id')
    def _onchange_standard_number(self):
        print("standard_number")

    # Listen event onchange country_state_code（地区コード）
    @api.onchange('country_state_code_id')
    @api.constrains('country_state_code_id')
    def _onchange_country_state_code(self):
        if self.country_state_code_id:
            self.country_state_name = self.country_state_code_id.name
        else:
            self.country_state_name = ''

    # Listen event onchange industry_code（業種コード）
    @api.onchange('industry_code_id')
    @api.constrains('industry_code_id')
    def _onchange_industry_code(self):
        if self.industry_code_id:
            self.industry_name = self.industry_code_id.name
        else:
            self.industry_name = ''

    # Listen event onchange supplier_group_code（取引先グループコード）
    @api.onchange('supplier_group_code_id')
    @api.constrains('supplier_group_code_id')
    def _onchange_supplier_group_code(self):
        if self.supplier_group_code_id:
            self.supplier_group_name = self.supplier_group_code_id.name
        else:
            self.supplier_group_name = ''

    # Listen event onchange customer_code_bill（請求先コード）
    @api.onchange('customer_code_bill_id')
    @api.constrains('customer_code_bill_id')
    def _onchange_customer_code_bill(self):
        if self.customer_code_bill_id:
            self.customer_name_bill = self.customer_code_bill_id.name
        else:
            self.customer_name_bill = ''

    # Listen event onchange customer_code（得意先コード）
    @api.onchange('customer_code_id')
    @api.constrains('customer_code_id')
    def _onchange_customer_code(self):
        if self.customer_code_id:
            self.customer_name = self.customer_code_id.name
        else:
            self.customer_name = ''

    # Listen event onchange recruitment_price（採用価格）
    @api.onchange('recruitment_price_id')
    @api.constrains('recruitment_price_id')
    def _onchange_recruitment_price(self):
        print("_onchange_recruitment_price")

    # compute code for fields
    def compute_maker_code(self):
        for line in self:
            line.maker_code = line.maker_id.search_key_freight

    def compute_class_lv1(self):
        for line in self:
            line.product_class_code_lv1 = line.product_class_code_lv1_id.product_class_code

    def compute_class_lv2(self):
        for line in self:
            line.product_class_code_lv2 = line.product_class_code_lv2_id.product_class_code

    def compute_class_lv3(self):
        for line in self:
            line.product_class_code_lv3 = line.product_class_code_lv3_id.product_class_code

    def compute_class_lv4(self):
        for line in self:
            line.product_class_code_lv4 = line.product_class_code_lv4_id.product_class_code

    def compute_jan_code(self):
        for line in self:
            line.jan_code = line.jan_code_id.barcode

    def compute_product_code(self):
        for line in self:
            line.product_code = line.product_code_id.product_code_1

    def compute_standard_number(self):
        for line in self:
            line.standard_number = line.standard_number_id.product_custom_standardnumber

    def compute_country_state_code(self):
        for line in self:
            line.country_state_code = line.country_state_code_id.code

    def compute_industry_code(self):
        for line in self:
            line.industry_code = line.industry_code_id.industry_code

    def compute_supplier_group_code(self):
        for line in self:
            line.supplier_group_code = line.supplier_group_code_id.partner_group_code

    def compute_customer_code_bill(self):
        for line in self:
            line.customer_code_bill = line.customer_code_bill_id.customer_code_bill

    def compute_customer_code(self):
        for line in self:
            line.customer_code = line.customer_code_id.customer_code

    def compute_recruitment_price(self):
        for line in self:
            line.recruitment_price = line.recruitment_price_id.price_1

    # compute code for 4 class lv name
    def compute_class_lv_all(self):
        for line in self:
            if line.product_class_code_lv1_id:
                line.product_class_name_lv1 = line.product_class_code_lv1_id.name
            else:
                line.product_class_name_lv1 = ''
            if line.product_class_code_lv2_id:
                line.product_class_name_lv2 = line.product_class_code_lv2_id.name
            else:
                line.product_class_name_lv2 = ''
            if line.product_class_code_lv3_id:
                line.product_class_name_lv3 = line.product_class_code_lv3_id.name
            else:
                line.product_class_name_lv3 = ''
            if line.product_class_code_lv4_id:
                line.product_class_name_lv4 = line.product_class_code_lv4_id.name
            else:
                line.product_class_name_lv4 = ''
