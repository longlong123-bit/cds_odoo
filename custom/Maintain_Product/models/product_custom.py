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

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.product"
    _rec_name = 'product_custom_search_key'
    _order = 'product_custom_search_key'

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id

    uom_id = fields.Many2one('uom.uom', 'UOM', default=_get_default_uom_id, required=True,
                             help="Default unit of measure used for all stock operations.")

    barcode = fields.Char(string='UPC/EAN', size=30)

    item_ids = fields.One2many('product.pricelist.item', 'product_id', 'Pricelist Items', copy=True)
    custom_attribute_line_ids = fields.One2many('product.custom.template.attribute.line', 'product_id',
                                                'Product Attributes', copy=True)
    seller_ids = fields.One2many('product.supplierinfo', 'product_id', 'Vendors', help="Define vendor pricelists.")

    product_custom_search_key = fields.Char('Search Key')
    product_custom_standardnumber = fields.Char('standardnumber')
    product_custom_goodsnamef = fields.Char('goodsnamef', size=30)
    product_custom_is_stocked = fields.Boolean('Stocked')
    product_custom_modelnumber = fields.Char('modelnumber')
    product_custom_freight_category = fields.Many2one('freight.category.custom', 'Freight Category')
    product_custom_comment_help = fields.Char('Comment/Help')
    product_custom_document_note = fields.Char('Document Note')
    product_custom_is_active = fields.Boolean('Active', default=True)
    write_date = fields.Datetime('Updated', readonly=True)
    product_custom_is_discontinued = fields.Boolean('Discontinued')
    product_custom_discontinued_at = fields.Date('Discontinued At')

    type = fields.Selection(
        [('asset', 'Asset'), ('expense_type', 'Expense type'), ('item', 'Item'), ('resource', 'Resource'),
         ('service', 'Service')], string='Product Type', default='item', required=True)

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
                'default_product_price_product_name': (self.product_custom_search_key or '') + '_' + (self.name or '')
            }
        }

    @api.constrains('barcode')
    def _check_barcode(self):
        if not re.match("^[0-9]*$", self.barcode):
            raise ValidationError("JAN/UPC/EANに英数をしてください。")
        return {}

    @api.model
    def create(self, values):
        # if create product without search key, generate new search key by sequence
        if not ('product_custom_search_key' in values):
            # get all search key is number
            self._cr.execute('''
                        SELECT product_custom_search_key
                        FROM product_product
                        WHERE product_custom_search_key ~ '^[0-9\.]+$';
                    ''')
            query_res = self._cr.fetchall()

            # generate new search key by sequence
            seq = self.env['ir.sequence'].next_by_code('product.product')
            # if new search key already exits, do again
            while seq in [res[0] for res in query_res]:
                seq = self.env['ir.sequence'].next_by_code('product.product')

            values['product_custom_search_key'] = seq

        self._check_data(values)

        product = super(ProductTemplate, self).create(values)

        self.env['product.custom.template.attribute.line'].create({
            'product_id': product.id,
            'product_cost_product_name': product.product_custom_search_key + '_' + product.name
        })

        return product

    def write(self, values):
        self._check_data(values)

        product = super(ProductTemplate, self).write(values)

        return product

    # Check validate, duplicate data
    def _check_data(self, values):
        # check Search Key
        if values.get('product_custom_search_key'):
            search_key_count = self.env['product.product'].search_count(
                [('product_custom_search_key', '=', values.get('product_custom_search_key'))])
            if search_key_count > 0:
                raise ValidationError(_('The Search Key has already been registered'))

        # check UPC/EAN
        if values.get('barcode'):
            barcode_count = self.env['product.product'].search_count([('barcode', '=', values.get('barcode'))])
            if barcode_count > 0:
                raise ValidationError(_('既に登録されています。'))

        return True


class ProductCustomTemplate(models.Model):
    _inherit = "product.template"

    name = fields.Char(size=255)


class ProductCustomPurchasingLine(models.Model):
    _inherit = "product.supplierinfo"
    _order = 'name'

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id
    product_purchasing_client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id
    uom_id = fields.Many2one('uom.uom', 'UOM', default=_get_default_uom_id, required=True,
                             help="Default unit of measure used for all stock operations.")

    name = fields.Many2one(string='Business Partner')
    product_code = fields.Char(string='Partner Product Key', default='1000000')
    product_purchasing_barcode = fields.Char('UPC/EAN*')
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
        values['product_name'] = (search_product.product_custom_search_key or '') + '_' + (search_product.name or '')
        values['product_code'] = search_product.product_custom_search_key or ''
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
