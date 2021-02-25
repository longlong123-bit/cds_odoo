# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, time, datetime
# from odoo import api, fields, models
# from odoo.exceptions import RedirectWarning
from addons.account.models.product import ProductTemplate
from odoo.tools.float_utils import float_round

# import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import re
from odoo.osv import expression
from lxml import etree

_logger = logging.getLogger(__name__)


class InheritProductTemplate(models.Model):
    _inherit = "product.template"
    property_account_income_id = fields.Many2one(default=lambda self: self.get_default_income_account())
    property_account_expense_id = fields.Many2one(default=lambda self: self.get_default_expenses_account())

    def get_default_income_account(self):
        account = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id),
                                                      ('internal_type', '=', 'other')], limit=1)
        return account.id

    def get_default_expenses_account(self):
        account = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id),
                                                      ('internal_type', '=', 'other')], limit=1)
        return account.id


class ProductTemplate(models.Model):
    _inherit = "product.product"
    _rec_name = 'product_code_1'
    _order = 'product_code_1'

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id

    uom_id = fields.Many2one('uom.uom', 'UOM', default=_get_default_uom_id,
                             help="Default unit of measure used for all stock operations.")
    product_uom_custom = fields.Char('uom')

    product_custom_freight_category = fields.Many2one('freight.category.custom', 'Maker code')
    product_maker_code = fields.Char('Maker code', related='product_custom_freight_category.search_key_freight')

    product_maker_name = fields.Char('Maker name', readonly=True, store=True)

    barcode = fields.Char(string='UPC/EAN', size=30, required=True)

    item_ids = fields.One2many('product.pricelist.item', 'product_id', 'Pricelist Items', copy=True)
    custom_attribute_line_ids = fields.One2many('product.custom.template.attribute.line', 'product_id',
                                                'Product Attributes', copy=True)
    seller_ids = fields.One2many('product.supplierinfo', 'product_id', 'Vendors', help="Define vendor pricelists.")

    # product_custom_search_key = fields.Char('Search Key')
    product_custom_standardnumber = fields.Char('standardnumber')
    product_custom_goodsnamef = fields.Char('goodsnamef', size=30)
    product_custom_is_stocked = fields.Boolean('Stocked')
    product_custom_modelnumber = fields.Char('modelnumber')
    product_custom_comment_help = fields.Char('Comment/Help')
    product_custom_document_note = fields.Char('Document Note')
    product_custom_is_active = fields.Boolean('Active', default=True)
    write_date = fields.Datetime('Updated')
    product_custom_is_discontinued = fields.Boolean('Discontinued')
    product_custom_discontinued_at = fields.Date('Discontinued At')
    # Product Class Code
    product_class_code_lv1 = fields.Many2one('product.class', string='Class code')
    product_class_code_lv2 = fields.Many2one('product.class', string='Class code')
    product_class_code_lv3 = fields.Many2one('product.class', string='Class code')
    product_class_code_lv4 = fields.Many2one('product.class', string='Class code')
    # Prodcuct Class Name
    product_class_name_lv1 = fields.Char('Class name', related="product_class_code_lv1.name")
    product_class_name_lv2 = fields.Char('Class name', related="product_class_code_lv2.name")
    product_class_name_lv3 = fields.Char('Class name', related="product_class_code_lv3.name")
    product_class_name_lv4 = fields.Char('Class name', related="product_class_code_lv4.name")
    # End
    product_code = fields.Char('Product code')
    product_code_1 = fields.Char('Product code 1')
    product_code_2 = fields.Char('Product code 2')
    product_code_3 = fields.Char('Product code 3')
    product_code_4 = fields.Char('Product code 4')
    product_code_5 = fields.Char('Product code 5')
    product_code_6 = fields.Char('Product code 6')
    price_no_tax_1 = fields.Float('Price no tax 1')
    price_no_tax_2 = fields.Float('Price no tax 2')
    price_no_tax_3 = fields.Float('Price no tax 3')
    price_no_tax_4 = fields.Float('Price no tax 4')
    price_no_tax_5 = fields.Float('Price no tax 5')
    price_no_tax_6 = fields.Float('Price no tax 6')
    price_include_tax_1 = fields.Float('Price include tax 1')
    price_include_tax_2 = fields.Float('Price include tax 2')
    price_include_tax_3 = fields.Float('Price include tax 3')
    price_include_tax_4 = fields.Float('Price include tax 4')
    price_include_tax_5 = fields.Float('Price include tax 5')
    price_include_tax_6 = fields.Float('Price include tax 6')
    setting_price = fields.Selection([('code_1', '商品コード1'), ('code_2', '商品コード2'), ('code_3', '商品コード3'),
                                      ('code_4', '商品コード4'), ('code_5', '商品コード5'), ('code_6', '商品コード6')],
                                     string='Setting price', default='code_1')

    cost = fields.Float('Cost')

    price_1 = fields.Float('Price 1')
    price_2 = fields.Float('Price 2')
    price_3 = fields.Float('Price 3')
    price_4 = fields.Float('Price 4')
    price_5 = fields.Float('Price 5')
    price_6 = fields.Float('Price 6')

    # Value according to setting
    price_by_setting = fields.Float('Price for setting')
    code_by_setting = fields.Char(string='Code for setting')

    # 消費税区分
    product_tax_category = fields.Selection(
        [('foreign', 'Foreign Tax'), ('internal', 'Internal Tax'), ('exempt', 'Tax Exempt')],
        # [('foreign', 'Foreign Tax'), ('internal', 'Internal Tax')],
        string='Tax Category*', default='foreign')

    standard_price = fields.Float('Standard price')
    price_no_tax = fields.Float('Price no tax')
    price_include_tax = fields.Float('Price include tax')
    original_price_no_tax = fields.Float('Original price no tax')
    original_price_include_tax = fields.Float('Original price include tax')

    flag_select = fields.Char('Flag select')
    model_number = fields.Char('Model number')
    model_name = fields.Char('Model name')
    # add extra field tax
    product_tax_id = fields.Many2one(
        string='Tax Rate',
        comodel_name='tax.tax',
        default=lambda self: self._get_default_tax(),
        ondelete='restrict'
    )
    product_tax_rate = fields.Float(
        string='Tax Rate',
        compute='_compute_tax_rate',
        store=True)

    type = fields.Selection(
        [('asset', 'Asset'), ('expense_type', 'Expense type'), ('item', 'Item'), ('resource', 'Resource'),
         ('service', 'Service')], string='Product Type', default='item')

    display_default_code = fields.Char(relation='product_code_1')

    product_total = fields.Char(string='assign_product')

    # Refer to open dialog get history of price
    refer_standard_price = fields.Many2one('account.move.line', store=False)

    def _get_default_tax(self):
        default_tax = self.env.ref('Maintain_Product.product_tax_10', False)
        tax_id = False
        if default_tax:
            tax_id = default_tax.id
        return tax_id

    @api.depends('product_tax_id')
    def _compute_tax_rate(self):
        for product in self:
            self.product_tax_rate = product.product_tax_id.amount or 0.0

    @api.onchange('refer_standard_price')
    def _onchange_refer_standard_price(self):
        if self.refer_standard_price:
            self.standard_price = self.refer_standard_price.price_unit

    # Setting product, when setting change or product change
    # Check if code_{i} then get product_code_{i}
    @api.constrains('product_code_1', 'product_code_2', 'product_code_3',
                    'product_code_4', 'product_code_5', 'product_code_6', 'setting_price')
    def set_code_by_setting(self):
        self.code_by_setting = ''
        for i in range(1, 7):
            if self.setting_price == ('code_' + str(i)):
                self.code_by_setting = self['product_code_' + str(i)]
                break

    @api.constrains('price_1', 'price_2', 'price_3',
                    'price_4', 'price_5', 'price_6', 'setting_price')
    def set_price_by_setting(self):
        self.price_by_setting = ''
        for i in range(1, 7):
            if self.setting_price == ('code_' + str(i)):
                self.price_by_setting = self['price_' + str(i)]
                break

    @api.constrains('product_code_1', 'product_code_2', 'product_code_3',
                    'product_code_4', 'product_code_5', 'product_code_6')
    def assign_product(self):
        for rec in self:
            rec.product_total = (rec.product_code_1 or '_') + '_' + (rec.product_code_2 or '_') + '_' + (
                    rec.product_code_3 or '_') + '_' + (rec.product_code_4 or '_') + '_' + (
                                        rec.product_code_5 or '_') + '_' + (rec.product_code_6 or '_')

    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            if self._context.get('show_product_code'):
                code = d.get('product_code_1')
                if code:
                    name = '[%s] %s' % (code, name)
                return (d['id'], name)
            if self._context.get('show_product_jan'):
                code = d.get('jan')
                if code:
                    name = '[%s] %s' % (code, name)
                return (d['id'], name)
                # name = '[%s] %s' % (code, name)
            else:
                code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
                if code:
                    name = '[%s] %s' % (code, name)
                return (d['id'], name)
                # name = '[%s] %s' % (code, name)
            # if code:
            #    code = d.get('product_code_1')
            #    print('3434343434343434')
            #    print(d)
            #    name = '[%s] %s' % (code, name)
            # return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = []
            if partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                            variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                    ) or False
                    mydict = {
                        'id': product.id,
                        'name': seller_variant or name,
                        'default_code': s.product_code or product.default_code,
                        'product_code_1': product.product_code_1,
                        'jan': product.barcode,
                    }
                    temp = _name_get(mydict)

                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                    'id': product.id,
                    'name': name,
                    'default_code': product.default_code,
                    'product_code_1': product.product_code_1,
                    'jan': product.barcode,
                }
                result.append(_name_get(mydict))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', context=None, limit=100):
        args = args or []
        recs = self.browse()
        if not recs:
            if self.env.context.get('show_code') == 'product_1':
                recs = self.search([('product_code_1', operator, name)] + args, limit=limit)
            elif self.env.context.get('show_code') == 'product_2':
                recs = self.search([('product_code_2', operator, name)] + args, limit=limit)
            elif self.env.context.get('show_code') == 'product_3':
                recs = self.search([('product_code_3', operator, name)] + args, limit=limit)
            elif self.env.context.get('show_code') == 'product_4':
                recs = self.search([('product_code_4', operator, name)] + args, limit=limit)
            elif self.env.context.get('show_code') == 'product_5':
                recs = self.search([('product_code_5', operator, name)] + args, limit=limit)
            elif self.env.context.get('show_code') == 'product_6':
                recs = self.search([('product_code_6', operator, name)] + args, limit=limit)
            elif self.env.context.get('show_jan_code') == 'ok':
                recs = self.search([('barcode', operator, name)] + args, limit=limit)
            else:
                recs = recs
        return recs.name_get()

    def open_pricelist(self):
        self.ensure_one()
        domain = ['|',
                  '&', ('product_tmpl_id', '=', self.product_tmpl_id.id), ('applied_on', '=', '1_product'),
                  '&', ('product_id', '=', self.id), ('applied_on', '=', '0_product_variant')]
        return {
            'name': 'Price',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'product.pricelist.item',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': domain,
            'context': {
                'default_product_id': self.id,
                'default_applied_on': '0_product_variant',
                'default_product_price_product_name': (self.product_code_1 or '') + '_' + (self.name or '')
            }
        }

    @api.constrains('barcode')
    def _check_barcode(self):
        if not re.match("^[0-9]*$", self.barcode):
            raise ValidationError("JAN/UPC/EANに数字のみを入力してください。")

        return {}

    @api.onchange('barcode')
    def _check_onchange_barcode(self):
        # check UPC/EAN
        if self.barcode:
            if not re.match("^[0-9]*$", self.barcode) or self.barcode == '000000000':
                raise ValidationError("JAN/UPC/EANに数字のみを入力してください。")

            if self.barcode == '0000000000000':
                ctx = self._context.copy()
                self.name = 'サンプル商品'
                uid = self.env['res.users'].search([('id', '=', ctx.get('uid'))])
                if not uid.has_group('base.group_erp_manager'):
                    raise ValidationError("既に登録されています。")

            barcode_count = self.env['product.product'].search_count([('barcode', '=', self.barcode)])
            if barcode_count > 0:
                raise ValidationError(_('既に登録されています。'))

        return {}

    # Check validate tax rate
    @api.constrains('product_tax_rate')
    def _check_maximum_day(self):
        if self.product_tax_rate < 0:
            raise ValidationError(_('The Tax Rate must be more than 0'))

    _sql_constraints = [
        ('name_code_uniq', 'unique(product_code_1,product_code_2, product_code_3, product_code_4, '
                           'product_code_5, product_code_6)', 'The code must be unique!')
    ]

    # @api.constrains('product_code_1', 'product_code_2', 'product_code_3',
    #                 'product_code_4', 'product_code_5', 'product_code_6')
    # def _check_unique_product_code(self):
    #     arr = [self.product_code_1, self.product_code_2, self.product_code_3,
    #            self.product_code_4, self.product_code_5, self.product_code_6]
    #     leng = len(arr)
    #
    #     for i in range(0, leng):
    #         for j in range(0, leng):
    #             if i != j and arr[i] and arr[i] == arr[j]:
    #                 raise ValidationError(_('Product_code is the same'))
    #
    #     for i in arr:
    #         if i:
    #             product_code_i = self._check_code('product_code_' + str(arr.index(i) + 1))
    #             print(i)
    #             exists = self.env['product.product'].search(
    #                 ['|', '|', '|', ('product_code_1', '=', i), ('product_code_2', '=', i),
    #                  '|', ('product_code_3', '=', i), ('product_code_5', '=', i),
    #                  '|', ('product_code_4', '=', i), ('product_code_6', '=', i),
    #                  ('id', '!=', self.id)])
    #             if exists:
    #                 raise ValidationError(_('Product_code must be unique'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'product_code_1': '', 'barcode': '000000000'})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
            default['barcode'] = False
        return super(ProductTemplate, self).copy(default)

    @api.onchange('product_custom_freight_category')
    def _get_product_custom_freight_category(self):
        for rec in self:
            if rec.product_custom_freight_category:
                rec.product_maker_name = rec.product_custom_freight_category.name

    # @api.model
    # def create(self, values):
    #     # if create product without search key, generate new search key by sequence
    #     if not ('product_code_1' in values):
    #         # get all search key is number
    #         self._cr.execute('''
    #                     SELECT product_code_1
    #                     FROM product_product
    #                     WHERE product_code_1 ~ '^[0-9\.]+$';
    #                 ''')
    #         query_res = self._cr.fetchall()
    #
    #         # generate new search key by sequence
    #         seq = self.env['ir.sequence'].next_by_code('product.product')
    #         # if new search key already exits, do again
    #         while seq in [res[0] for res in query_res]:
    #             seq = self.env['ir.sequence'].next_by_code('product.product')
    #
    #         values['product_code_1'] = seq
    #     for i in range(1, 7):
    #         product_code = self._check_product_code(values, 'product_code_' + str(i))
    #         # product_code = self._check_product_code('product_code_' + str(i))
    #         if product_code in values:
    #             self._cr.execute('''
    #                         SELECT *
    #                         FROM
    #                         (
    #                             SELECT product_code_1 as product_code FROM product_product
    #                             UNION ALL
    #                             SELECT product_code_2 as product_code FROM product_product
    #                             UNION ALL
    #                             SELECT product_code_3 as product_code FROM product_product
    #                             UNION ALL
    #                             SELECT product_code_4 as product_code FROM product_product
    #                             UNION ALL
    #                             SELECT product_code_5 as product_code FROM product_product
    #                             UNION ALL
    #                             SELECT product_code_6 as product_code FROM product_product
    #                         )temp_table WHERE temp_table.product_code is not null;
    #                         ''')
    #
    #         query_res = self._cr.fetchall()
    #         if values.get(product_code) in [res[0] for res in query_res]:
    #             print('trung')
    #             raise ValidationError(_('Product_code has already been registered'))
    #         else:
    #             print('ko trung')
    #
    #     # generate new search key by sequence
    #     seq = self.env['ir.sequence'].next_by_code('product.product')
    #     # if new search key already exits, do again
    #     while seq in [res[0] for res in query_res]:
    #         seq = self.env['ir.sequence'].next_by_code('product.product')
    #
    #     self._check_data(values)
    #
    #     self._set_list_price(values)
    #
    #     # self.assign_product()
    #
    #     product = super(ProductTemplate, self).create(values)
    #
    #     self.env['product.custom.template.attribute.line'].create({
    #         'product_id': product.id,
    #         'product_cost_product_name': (product.product_code_1 or '') + '_' + (product.name or '')
    #     })
    #
    #     return product

    def _check_product_code(self, values, product_code):
        # print(values[product_code])
        return product_code

    def _check_code(self, product_code):
        return product_code

    def _set_list_price(self, values):
        if 'setting_price' in values:
            def setting_value(index):
                switcher = {
                    'code_1': 'price_no_tax_1',
                    'code_2': 'price_no_tax_2',
                    'code_3': 'price_no_tax_3',
                    'code_4': 'price_no_tax_4',
                    'code_5': 'price_no_tax_5',
                    'code_6': 'price_no_tax_6'
                }
                return switcher.get(index, 'price_no_tax_1')

            values['list_price'] = values[setting_value(values['setting_price'])]
        return True

        self._check_data(values)

        product = super(ProductTemplate, self).write(values)

        return product

    # Check validate, duplicate data
    def _check_data(self, values):
        # check Search Key
        if values.get('product_code_1'):
            search_key_count = self.env['product.product'].search_count(
                [('product_code_1', '=', values.get('product_code_1'))])
            if search_key_count > 0:
                raise ValidationError(_('The Search Key has already been registered'))

        # check UPC/EAN
        if values.get('barcode'):
            barcode_count = self.env['product.product'].search_count([('barcode', '=', values.get('barcode'))])
            if barcode_count > 0:
                raise ValidationError(_('既に登録されています。'))

        return True

    @api.onchange('product_tax_category')
    def _onchange_product_tax_category(self):
        if self.product_tax_category == 'exempt':
            self.update({'product_tax_id': False,
                         'product_tax_rate': 0.0})

    @api.onchange('product_code_1', 'price_1', 'price_no_tax_1', 'price_include_tax_1',
                  'product_code_2', 'price_2', 'price_no_tax_2', 'price_include_tax_2',
                  'product_code_3', 'price_3', 'price_no_tax_3', 'price_include_tax_3',
                  'product_code_4', 'price_4', 'price_no_tax_4', 'price_include_tax_4',
                  'product_code_5', 'price_5', 'price_no_tax_5', 'price_include_tax_5',
                  'product_code_6', 'price_6', 'price_no_tax_6', 'price_include_tax_6',
                  'product_tax_category', 'product_tax_rate')
    def _onchange_tax(self):
        for rec in self:
            for i in range(1, 7):
                if rec['product_tax_category'] == 'foreign':
                    rec['price_no_tax_' + str(i)] = rec['price_' + str(i)]
                    rec['price_include_tax_' + str(i)] = rec['price_no_tax_' + str(i)] * (
                            rec.product_tax_rate / 100 + 1)
                elif rec['product_tax_category'] == 'internal':
                    rec['price_include_tax_' + str(i)] = rec['price_' + str(i)]
                    rec['price_no_tax_' + str(i)] = rec['price_include_tax_' + str(i)] / (
                            rec.product_tax_rate / 100 + 1)
                else:
                    rec['price_no_tax_' + str(i)] = rec['price_include_tax_' + str(i)] = rec['price_' + str(i)]

    @api.onchange('product_class_code')
    def _get_product_class_name(self):
        for rec in self:
            if rec.product_class_code:
                rec.product_class_name = rec.product_class_code.name

    @api.constrains('cost', 'price_1', 'price_2', 'price_3', 'price_4', 'price_5', 'price_6',
                    'price_no_tax_1', 'price_no_tax_2', 'price_no_tax_3', 'price_no_tax_4', 'price_no_tax_5',
                    'price_no_tax_6', 'price_include_tax_1', 'price_include_tax_2', 'price_include_tax_3',
                    'price_include_tax_4', 'price_include_tax_5', 'price_include_tax_6', 'original_price_no_tax',
                    'original_price_include_tax', 'standard_price', 'list_price', 'price_no_tax', 'price_include_tax')
    def _check_negative_price(self):
        arr = [self.price_1, self.price_2, self.price_3, self.price_4, self.price_5, self.price_6,
               self.price_no_tax_1, self.price_no_tax_2, self.price_no_tax_3, self.price_no_tax_4, self.price_no_tax_5,
               self.price_no_tax_6, self.price_include_tax_1, self.price_include_tax_2, self.price_include_tax_3,
               self.price_include_tax_4, self.price_include_tax_5, self.price_include_tax_6, self.original_price_no_tax,
               self.original_price_include_tax, self.standard_price, self.list_price, self.price_no_tax,
               self.price_include_tax, self.cost]
        leng = len(arr)
        for i in range(0, leng):
            if arr[i] < 0:
                raise ValidationError(_('Price must be greater than 0 !'))

    # Xử lý phân loại product
    @api.onchange('product_class_code_lv1')
    @api.depends('product_class_code_lv1')
    def _get_chidren_class_lv1(self):
        self.product_class_code_lv2 = False
        domain = {}
        class_list = []
        if self.product_class_code_lv1:
            children_obj = self.env['product.class'].search(
                [('product_parent_code.product_class_code', '=', self.product_class_code_lv1.product_class_code)])
            for children_ids in children_obj:
                class_list.append(children_ids.id)
            # to assign parter_list value in domain
            domain = {'product_class_code_lv2': [('id', '=', class_list)]}
        return {'domain': domain}

    @api.onchange('product_class_code_lv2')
    def _get_chidren_class_lv2(self):
        self.product_class_code_lv3 = False
        domain = {}
        class_list = []
        if self.product_class_code_lv2:
            children_obj = self.env['product.class'].search(
                [('product_parent_code.product_class_code', '=', self.product_class_code_lv2.product_class_code)])
            for children_ids in children_obj:
                class_list.append(children_ids.id)
            # to assign parter_list value in domain
            domain = {'product_class_code_lv3': [('id', '=', class_list)]}
        return {'domain': domain}

    @api.onchange('product_class_code_lv3')
    def _get_chidren_class_lv3(self):
        self.product_class_code_lv4 = False
        domain = {}
        class_list = []
        if self.product_class_code_lv3:
            children_obj = self.env['product.class'].search(
                [('product_parent_code.product_class_code', '=', self.product_class_code_lv3.product_class_code)])
            for children_ids in children_obj:
                class_list.append(children_ids.id)
            # to assign parter_list value in domain
            domain = {'product_class_code_lv4': [('id', '=', class_list)]}
        return {'domain': domain}

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        odoo/models.py
        """
        ctx = self._context.copy()
        # han-lh comment - update domain for product - start
        if ctx.get('product_master_module'):
            sample_product_jancode = '0000000000000'
            uid = self.env['res.users'].search([('id', '=', ctx.get('uid'))])
            if not uid.has_group('base.group_erp_manager'):
                args += [['barcode', '!=', sample_product_jancode]]
            else:
                if ['barcode', '!=', sample_product_jancode] in args:
                    args.remove(['barcode', '!=', sample_product_jancode])
        # han-lh comment - update domain for product - end
        if ctx.get('limit') and args:
            limit = ctx['limit']
        if ctx.get('have_advance_search'):
            domain = []
            check = 0
            arr = ["barcode", "product_maker_name", "product_custom_standardnumber", "name",
                   "product_custom_goodsnamef"]
            for se in args:
                if se[0] == '&':
                    continue
                if se[0] == 'search_category' and se[2] == 'equal':
                    check = 1
                if check == 1 and se[0] == 'product_total':
                    domain += ['|', '|', '|', '|', '|', ("product_code_1", "=ilike", se[2]),
                               ("product_code_2", "=ilike", se[2]), ("product_code_3", "=ilike", se[2]),
                               ("product_code_4", "=ilike", se[2]), ("product_code_5", "=ilike", se[2]),
                               ("product_code_6", "=ilike", se[2])]
                if check == 1 and se[0] in arr:
                    se[1] = '=ilike'
                if se[0] != 'search_category':
                    domain += [se]
            args = domain
        res = super(ProductTemplate, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res


class ProductCustomTemplate(models.Model):
    _inherit = "product.template"

    name = fields.Char(size=255, required=True)
    product_code_1 = fields.Char('Product code 1')


class ProductCustomPurchasingLine(models.Model):
    _inherit = "product.supplierinfo"
    _order = 'name'

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id

    product_purchasing_client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id

    uom_id = fields.Many2one('uom.uom', 'UOM', default=_get_default_uom_id,
                             help="Default unit of measure used for all stock operations.")
    product_uom_custom = fields.Char('uom')

    name = fields.Many2one(string='Business Partner')
    product_code = fields.Char(string='Partner Product Key', default='1000000')
    product_purchasing_barcode = fields.Char('UPC/EAN')
    product_purchasing_quality_rating = fields.Integer('Quality rating')
    product_purchasing_is_current_vendor = fields.Boolean('Current vendor', default=True)
    product_purchasing_po_price = fields.Float('PO Price')
    product_purchasing_price_effective = fields.Date('Price effective')
    product_purchasing_royalty_amount = fields.Float('Royalty Amount')
    product_purchasing_last_po_price = fields.Float('Last PO Price', readonly=True)
    product_purchasing_last_invoice_price = fields.Float('Last Invoice Price', readonly=True)
    product_purchasing_order_pack_qty = fields.Float('Order Pack Qty')
    product_purchasing_actual_delivery_time = fields.Integer('Actual Delivery Time', readonly=True)
    product_purchasing_cost_per_order = fields.Float('Cost per Order')
    product_purchasing_partner_category = fields.Char('Partner Category')
    product_purchasing_manufacturer = fields.Char('Manufacturer')
    product_purchasing_is_active = fields.Boolean('Active', default=True)
    product_purchasing_is_discontinued = fields.Boolean('Discontinued')
    product_purchasing_discontinued_at = fields.Date('Discontinued At')

    price = fields.Float('Price', default=0.0, digits='Product Price',
                         required=True, help="The price to purchase a product")
    delay = fields.Integer('Delivery Lead Time', default=1, required=True)
    min_qty = fields.Float('Quantity', default=0.0, required=True)

    @api.constrains('price', 'product_purchasing_po_price', 'min_qty', 'delay', 'product_purchasing_order_pack_qty')
    def _check_negative_price(self):
        arr = [self.price, self.product_purchasing_po_price, self.min_qty,
               self.delay, self.product_purchasing_order_pack_qty]
        leng = len(arr)
        for i in range(0, leng):
            if arr[i] < 0:
                raise ValidationError(_('Price must be greater than 0 !'))

    def button_details(self):
        view = {
            'name': _('Detail'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.supplierinfo',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': True,
            'res_id': self.id,
        }
        return view

    @api.model
    def create(self, values):
        self._check_data(values)

        search_product = self.env['product.product'].search([('id', '=', values['product_id'])], limit=1)
        values['product_name'] = (search_product.product_code_1 or '') + '_' + (search_product.name or '')
        values['product_code'] = search_product.product_code_1 or ''
        purchasing = super(ProductCustomPurchasingLine, self).create(values)

        return purchasing

    def write(self, values):
        self._check_data(values)

        purchasing = super(ProductCustomPurchasingLine, self).write(values)

        return purchasing

    def action_close_dialog(self):
        return {'type': 'ir.actions.act_window_close'}

    # Check validate, duplicate data
    def _check_data(self, values):
        # check Business Partner is exist
        self._check_business_partner(values)

        # check current vendor is exist
        self._check_current_vendor(values)

        return True

    # Check current vendor is exist
    def _check_current_vendor(self, values):
        if values.get('product_purchasing_is_active') and values.get('product_purchasing_is_current_vendor'):
            condition = [('product_purchasing_is_current_vendor', '=', True)]
            # when create, values.get('product_id') is exits
            # when edit, only field that changed has new value, other field keep old value in self
            if values.get('product_id'):
                condition.append(('product_id', '=', values.get('product_id')))
            else:
                condition.append(('product_id', '=', self.product_id.id))

            product_purchasing_count = self.env['product.supplierinfo'].search_count(condition)
            if product_purchasing_count > 0:
                raise ValidationError(
                    _('Could not save changes: Could not save record - Require unique data: Current vendor'))
        else:
            return True

    # Check Business Partner is exist
    def _check_business_partner(self, values):
        if values.get('name'):
            condition = [('name', '=', values.get('name'))]
            # when create, values.get('product_id') is exits
            # when edit, only field that changed has new value, other field keep old value in self
            if values.get('product_id'):
                condition.append(('product_id', '=', values.get('product_id')))
            else:
                condition.append(('product_id', '=', self.product_id.id))

            product_purchasing_count = self.env['product.supplierinfo'].search_count(condition)
            if product_purchasing_count > 0:
                raise ValidationError(
                    _('Could not save record - Require unique data: - Please change information.'))
        return True


class ProductCustomPrice(models.Model):
    _inherit = "product.pricelist.item"
    _order = 'pricelist_id'

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id

    product_price_client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)

    fixed_price = fields.Float(string='List Price')
    product_price_company_id = fields.Many2one('res.company', 'Organization', default=lambda self: self.env.company.id,
                                               index=1)
    pricelist_id = fields.Many2one(string='Price List Version')
    product_price_product_name = fields.Char('Product*', readonly=True)
    product_price_standard_price = fields.Float('Standard Price')
    product_price_limit_price = fields.Float('Limit Price')
    product_price_is_active = fields.Boolean('Active', default=True)

    def button_details(self):
        view = {
            'name': _('Detail'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.pricelist.item',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': True,
            'res_id': self.id,
        }
        return view

    @api.model
    def create(self, values):
        self._check_data(values)

        price = super(ProductCustomPrice, self).create(values)

        return price

    def write(self, values):
        self._check_data(values)

        price = super(ProductCustomPrice, self).write(values)

        return price

    def action_close_dialog(self):
        return {'type': 'ir.actions.act_window_close'}

    # Check validate, duplicate data
    def _check_data(self, values):
        self._check_price_list_version()

        return True

    # Check duplicate Price List Version
    @api.constrains('pricelist_id')
    def _check_price_list_version(self):
        product_pricelist_item_count = self.env['product.pricelist.item'].search_count(
            [('product_id', '=', self.product_id.id), ('pricelist_id', '=', self.pricelist_id.id)])

        if product_pricelist_item_count > 1:
            raise ValidationError(
                _('Could not save record - Require unique data: - Please change information.'))

        return True


class ProductTemplateAttributeLine(models.Model):
    _name = "product.custom.template.attribute.line"

    product_id = fields.Many2one('product.product', string="Product Product", ondelete='cascade',
                                 required=True, index=True)

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id

    product_cost_client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, index=1)
    product_cost_product_name = fields.Char('Product*', readonly=True)
    product_cost_attribute_info = fields.Char('Attribute Info', readonly=True)
    product_cost_accounting_schema = fields.Char('Accounting Schema*', required=True, default='ベース会計スキーマ')
    product_cost_cost_type = fields.Char('Cost Type*', required=True, default='OSS ERP Solutions プライマリ原価タイプ')
    product_cost_cost_element = fields.Char('Cost Element*', required=True, default='標準原価')
    product_cost_description = fields.Text('Description')
    product_cost_current_cost_price = fields.Float('Current Cost Price*')
    product_cost_current_cost_price_lower_level = fields.Float('Current Cost Price Lower Level*', readonly=True)
    product_cost_future_cost_price = fields.Float('Future Cost Price*')
    product_cost_future_cost_price_lower_level = fields.Float('Future Cost Price Lower Level', readonly=True)
    product_cost_current_quantity = fields.Integer('Current Quantity*', readonly=True)
    product_cost_is_cost_frozen = fields.Boolean('Cost Frozen')
    product_cost_accumulated_qty = fields.Integer('Accumulated Qty', readonly=True)
    product_cost_accumulated_amt = fields.Integer('Accumulated Amt', readonly=True)
    product_cost_is_active = fields.Boolean('Active', default=True)

    product_cost_costing_method = fields.Char('Costing Method', readonly=True)
    product_cost_percent = fields.Integer('Percent', readonly=True)
    product_cost_is_processed = fields.Boolean('Processed', readonly=True)

    @api.constrains('product_cost_future_cost_price')
    def _check_negative_price(self):
        arr = [self.product_cost_future_cost_price]
        leng = len(arr)
        for i in range(0, leng):
            if arr[i] < 0:
                raise ValidationError(_('Price must be greater than 0 !'))

    def button_details(self):
        view = {
            'name': _('Detail'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.custom.template.attribute.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': True,
            'res_id': self.id,
        }
        return view

    def action_close_dialog(self):
        return {'type': 'ir.actions.act_window_close'}


class ClassFreightCategory(models.Model):
    _inherit = 'freight.category.custom'

    def name_get(self):
        super(ClassFreightCategory, self).name_get()
        data = []
        for row in self:
            display_value = row.search_key_freight if 'showcode' in self.env.context or 'master_price_list' in self.env.context else row.name
            data.append((row.id, display_value))
        return data
