# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class ClassMasterPriceList(models.Model):
    _name = 'master.price.list'

    # Relational fields with another model
    maker_id = fields.Many2one('freight.category.custom', string="Maker Code")
    product_id = fields.Many2one('product.product', string="Product Id")

    # メーカーCD
    maker_code = fields.Char(string="Maker Code")

    # メーカー名
    maker_name = fields.Char('Maker Name')

    # 商品大分類CD
    product_class_code_lv1_id = fields.Many2one('product.class', string="Main Category Code")
    product_class_code_lv1 = fields.Char(string='Main Category Code')

    # 大分類名
    product_class_name_lv1 = fields.Char(string="Main Category Name")

    # 商品中分類CD
    product_class_code_lv2_id = fields.Many2one('product.class', string="Middle Category Code")
    product_class_code_lv2 = fields.Char(string="Middle Category Code")

    # 中分類名
    product_class_name_lv2 = fields.Char(string="Middle Category Name")

    # 商品中小分類CD
    product_class_code_lv3_id = fields.Many2one('product.class', string="Middle Small Category Code")
    product_class_code_lv3 = fields.Char(string="Middle Small Category Code")

    # 中小分類名
    product_class_name_lv3 = fields.Char(string="Middle Small Category Name")

    # 商品小分類CD
    product_class_code_lv4_id = fields.Many2one('product.class', string="Small Category Code")
    product_class_code_lv4 = fields.Char(string="Small Category Code")

    # 小分類名
    product_class_name_lv4 = fields.Char(string="Small Category Name")

    # JANコード
    jan_code_id = fields.Many2one('product.product', string="JAN Code")
    jan_code = fields.Char(string="JAN Code")

    # 商品コード
    product_code_id = fields.Many2one('product.product', string="Product Code")
    product_code_select = fields.Selection(
        [('product_1', 'product code 1'), ('product_2', 'product code 2'), ('product_3', 'product code 3'),
         ('product_4', 'product code 4'), ('product_5', 'product code 5'), ('product_6', 'product code 6')],
        string='Product Code Select')
    product_code = fields.Char(string="Product Code")

    # 品番 / 型番
    # standard_number_id = fields.Many2one('product.product', string="Standard Number")
    standard_number = fields.Char(string="Standard Number")

    # 商品名
    product_name = fields.Char(string="Product Name", store=True)

    # 地区コード
    country_state_code_id = fields.Many2one('res.country.state', string="Country State Code",
                                            domain=[('country_id.code', '=', 'JP')])
    country_state_code = fields.Char(string="Country State Code")

    # 地区名
    country_state_name = fields.Char(string="Country State Name", store=True)

    # 業種コード
    industry_code_id = fields.Many2one('res.partner.industry', string="Industry Code")
    industry_code = fields.Char(string="Industry Code")

    # 業種名
    industry_name = fields.Char(string="Industry Name", store=True)

    # 取引先グループコード
    supplier_group_code_id = fields.Many2one('business.partner.group.custom', string="Supplier Group Code")
    supplier_group_code = fields.Char(string="Supplier Group Code")

    # 取引先グループ名
    supplier_group_name = fields.Char(string="Supplier Group Name", store=True)

    # 請求先コード
    customer_code_bill_id = fields.Many2one('res.partner', string="Customer Code Bill")
    customer_code_bill = fields.Char(string="Customer Code Bill")

    # 請求先名
    customer_name_bill = fields.Char(string="Customer Name Bill", store=True)

    # 得意先コード
    customer_code_id = fields.Many2one('res.partner', string="Customer Code")
    customer_code = fields.Char(string="Customer Code")

    # 得意先名
    customer_name = fields.Char(string="Customer Name", store=True)

    # 採用価格
    recruitment_price_select = fields.Selection(
        [('standard_price', 'Standard Price'), ('price_1', 'Price')],
        string='Recruitment Price')

    # 掛率
    rate = fields.Float(string="Rate")

    # 適用売価
    price_applied = fields.Float(string="Price Applied")

    # 適用年月日
    date_applied = fields.Date(string="Date Applied", default=datetime.today())

    # Listen event onchange maker_code (メーカーCD)
    @api.onchange('maker_id')
    def _onchange_maker(self):
        if self.maker_id:
            self.maker_name = self.maker_id.name
            self.maker_code = self.maker_id.search_key_freight
        else:
            self.maker_name = ''

    # Listen event onchange product_class_code_lv1
    @api.onchange('product_class_code_lv1_id')
    def _onchange_product_class_code_lv1(self):
        if self.product_class_code_lv1_id:
            # Set value for product_class_name_lv1 fields
            self.product_class_name_lv1 = self.product_class_code_lv1_id.name
            self.product_class_code_lv1 = self.product_class_code_lv1_id.product_class_code

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
            self.product_class_code_lv1 = ''

    # Listen event onchange product_class_code_lv2
    @api.onchange('product_class_code_lv2_id')
    def _onchange_product_class_code_lv2(self):
        if self.product_class_code_lv2_id:
            # Set value for product_class_name_lv2 fields
            self.product_class_code_lv2 = self.product_class_code_lv2_id.product_class_code
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
            self.product_class_code_lv2 = ''

    # Listen event onchange product_class_code_lv3
    @api.onchange('product_class_code_lv3_id')
    def _onchange_product_class_code_lv3(self):
        if self.product_class_code_lv3_id:
            # Set value for product_class_name_lv3 fields
            self.product_class_name_lv3 = self.product_class_code_lv3_id.name
            self.product_class_code_lv3 = self.product_class_code_lv3_id.product_class_code

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
            self.product_class_code_lv3 = ''

    # Listen event onchange product_class_code_lv4
    @api.onchange('product_class_code_lv4_id')
    def _onchange_product_class_code_lv4(self):
        if self.product_class_code_lv4_id:
            # Set value for product_class_name_lv4 fields
            self.product_class_name_lv4 = self.product_class_code_lv4_id.name
            self.product_class_code_lv4 = self.product_class_code_lv4_id.product_class_code
        else:
            self.product_class_name_lv4 = ''
            self.product_class_code_lv4 = ''

    # Listen event onchange jan_code （JANコード）
    @api.onchange('jan_code_id')
    def _onchange_jan_code(self):
        self.product_code_id = False

        if self.jan_code_id:
            self.jan_code = self.jan_code_id.barcode
            self.product_name = self.jan_code_id.name
            # self.product_code = self.jan_code_id.product_code_1
            self.product_code_select = 'product_1'
            self.recruitment_price_select = 'standard_price'

            product_code_child = self.env['product.product'].search([('barcode', '=', self.jan_code)])
            product_code_id = product_code_child.ids
            domain = {'product_code_id': [('id', '=', product_code_id)],}
        else:
            self.jan_code = self.product_name = ''
            self.product_code_select = False
            self.recruitment_price_select = False
            self.product_code = ''
            domain = {'product_code_id': []}
        return {'domain': domain}

    @api.onchange('product_code_select')
    def _onchange_product_code_select(self):
        self.product_code_id = False
        self.product_code = ''

    # Listen event onchange product_code （商品コード）
    @api.onchange('product_code_id')
    def _onchange_product_code(self):
        if self.product_code_id:
            if self.product_code_select == 'product_1':
                self.product_code = self.product_code_id.product_code_1
            elif self.product_code_select == 'product_2':
                self.product_code = self.product_code_id.product_code_2
            elif self.product_code_select == 'product_3':
                self.product_code = self.product_code_id.product_code_3
            elif self.product_code_select == 'product_4':
                self.product_code = self.product_code_id.product_code_4
            elif self.product_code_select == 'product_5':
                self.product_code = self.product_code_id.product_code_5
            elif self.product_code_select == 'product_6':
                self.product_code = self.product_code_id.product_code_6
            else:
                self.product_code = ''
            self.product_name = self.product_code_id.name
        else:
            self.product_code = ''
            if not self.jan_code_id:
                self.product_name = ''

    # Listen event onchange country_state_code（地区コード）
    @api.onchange('country_state_code_id')
    def _onchange_country_state_code(self):
        if self.country_state_code_id:
            self.country_state_name = self.country_state_code_id.name
            self.country_state_code = self.country_state_code_id.code
        else:
            self.country_state_code = self.country_state_name = ''

    # Listen event onchange industry_code（業種コード）
    @api.onchange('industry_code_id')
    def _onchange_industry_code(self):
        if self.industry_code_id:
            self.industry_name = self.industry_code_id.name
            self.industry_code = self.industry_code_id.industry_code
        else:
            self.industry_code = self.industry_name = ''

    # Listen event onchange supplier_group_code（取引先グループコード）
    @api.onchange('supplier_group_code_id')
    def _onchange_supplier_group_code(self):
        if self.supplier_group_code_id:
            self.supplier_group_name = self.supplier_group_code_id.name
            self.supplier_group_code = self.supplier_group_code_id.partner_group_code
        else:
            self.supplier_group_code = self.supplier_group_name = ''

    # Listen event onchange customer_code_bill（請求先コード）
    @api.onchange('customer_code_bill_id')
    def _onchange_customer_code_bill(self):
        if self.customer_code_bill_id:
            self.customer_name_bill = self.customer_code_bill_id.name
            self.customer_code_bill = self.customer_code_bill_id.customer_code_bill
            self.customer_code_id = False

            # set domain for customer code
            customer_code_child = self.env['res.partner'].search([('customer_code_bill', '=', self.customer_code_bill)])
            customer_code = customer_code_child.ids
            domain = {'customer_code_id': [('id', '=', customer_code)]}
            return {'domain': domain}
        else:
            self.customer_code_bill = self.customer_name_bill = ''

    # Listen event onchange customer_code（得意先コード）
    @api.onchange('customer_code_id')
    def _onchange_customer_code(self):
        if self.customer_code_id:
            self.customer_name = self.customer_code_id.name
            self.customer_code = self.customer_code_id.customer_code
        else:
            self.customer_code = self.customer_name = ''

    _sql_constraints = [('master.price.list', 'unique(maker_id, product_class_code_lv1_id, product_class_code_lv2_id, product_class_code_lv3_id, product_class_code_lv4_id, jan_code_id, product_code_id, country_state_code_id, supplier_group_code_id, country_state_code_id, industry_code_id, supplier_group_code_id, customer_code_bill_id, customer_code_id, recruitment_price_select, date_applied)', 'This data has been existed.')]

