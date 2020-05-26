# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import operator
from datetime import timedelta, time, datetime
from addons.account.models.product import ProductTemplate
from odoo.tools.float_utils import float_round

import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import re
from odoo.osv import expression
from operator import attrgetter, itemgetter

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
    # partner_id = fields.Many2one(string='Partner Order')

    document_no = fields.Char(string='Document No')
    document_reference = fields.Char(string='Document No Reference', store=False)

    expiration_date = fields.Date(string='Expiration Date')
    comment = fields.Text(string='Comment')
    # is_unit_quotations = fields.Boolean(string='Unit Quotations')
    quotation_type = fields.Selection([
        ('unit', 'Unit Quotation'),
        ('normal', 'Normal Quotation')
    ], string='Unit/Normal Quotation', default='normal')
    is_print_date = fields.Boolean(string='Print Date')
    tax_method = fields.Selection([
        ('no_tax', '非課税'),
        ('foreign_tax', '外税／明細'),
        ('voucher', '伝票'),
        ('invoice', '請求'),
        ('internal_tax', '内税／明細'),
        ('custom_tax', '税調整別途')
    ], string='Tax Method', default='no_tax')
    quotations_date = fields.Date(string='Quotations Date')
    order_id = fields.Many2one('sale.order', string='Order', store=False)
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
    report_header = fields.Many2one('sale.order.reportheader', string='Report Header')
    # report_header = fields.Selection([
    #     ('quotation', 'Quotation'),
    #     ('invoice', 'Invoice'),
    #     ('sale', 'Sale')
    # ], string='Report Header', readonly=False, default='quotation')
    paperformat_id = fields.Many2one(related='company_id.paperformat_id', string='Paper Format')

    sale_custom_id = fields.Many2one('sale.custom', string="Sale Custom", ondelete='cascade', required=True, index=True)

    @api.onchange('partner_id')
    def _get_detail_product(self):
        if self.partner_id:
            for rec in self:
                rec.partner_id = self.partner_id or ''
                rec.partner_name = self.partner_id.name or ''

    @api.model
    def create(self, values):
        # set document_no
        if (not ('document_no' in values)) or (not values['document_no']):
            # get all document no. is number
            self._cr.execute('''
                            SELECT document_no
                            FROM sale_order
                            WHERE SUBSTRING(document_no, 5) ~ '^[0-9\.]+$';
                        ''')
            query_res = self._cr.fetchall()

            # generate new document no. by sequence
            seq = self.env['ir.sequence'].next_by_code('sale.order')
            # if new document no. already exits, do again
            while seq in [res[0] for res in query_res]:
                seq = self.env['ir.sequence'].next_by_code('sale.order')

            values['document_no'] = seq

        # self._check_data(values)
        # TODO set report header
        if 'report_header' in values:
            self.env.company.report_header = values.get('report_header')
            # self.env.company.report_header = dict(self._fields['report_header'].selection).get(
            #     values.get('report_header'))
        else:
            self.env.company.report_header = ''

        quotations_custom = super(QuotationsCustom, self).create(values)

        return quotations_custom

    def write(self, values):
        # self._check_data(values)
        # TODO set report header
        if 'report_header' in values:
            self.env.company.report_header = values.get('report_header')
            # self.env.company.report_header = dict(self._fields['report_header'].selection).get(
            #     values.get('report_header'))

        quotations_custom = super(QuotationsCustom, self).write(values)

        return quotations_custom

    # TODO get document no
    # def _get_docment_no(self, document_no):
    #     return ''

    def open_popup(self, **kwargs):
        # self.ensure_one()
        # raise ValidationError(_('test abcd'))
        # return request.render('todo_website.hello')
        # domain = ['|',
        #           '&', ('product_tmpl_id', '=', self.product_tmpl_id.id), ('applied_on', '=', '1_product'),
        #           '&', ('product_id', '=', self.id), ('applied_on', '=', '0_product_variant')]
        return {
            'name': 'test',
            'view_mode': 'list',
            'view_type': 'list',
            # 'priority': '3',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'target': 'new',
            # 'domain': domain,
            # 'context': {
            #     'default_product_id': self.id,
            #     'default_applied_on': '0_product_variant',
            #     'default_product_price_product_name': (self.product_custom_search_key or '') + '_' + (self.name or '')
            # }
        }

    @api.model
    def test_js(self, testValue):
        # raise ValidationError(_('test js'))
        # if testValue:

        return 'test js: ' + str(testValue)

    @api.model
    def get_detail_order(self, order_id, fieldsSelect):
        # TODO get dict form js
        # fieldInfo = {'id': 100, 'name': 200, 'document_no': 300, 'shipping_address': 300, 'expected_date': 300}
        # for (k, v) in yArray.items():
        #     print(k, v)

        # set field to search data
        fields_select = ', '.join(fieldsSelect)
        self._cr.execute('''
                    SELECT ''' + str(fields_select) + '''
                    FROM sale_order
                    WHERE id = ''' + str(order_id) + '''
                    LIMIT 1;
                ''')
        query_res = self._cr.fetchall()
        # print(' - '.join([str(res[0]) for res in query_res]))

        # convert result to dict
        tuple_key = tuple(fieldsSelect)
        for value in query_res:
            res = {tuple_key[i]: value[i] for i, _ in enumerate(value)}

        # return [res for res in query_res]
        return res

    @api.model
    def search_order(self, args=None, name='', limit=100, name_get_uid=None):

        # yArray = {'id1': 100, 'id2': 200, "tag with spaces": 300}
        # for (k, v) in yArray.items():
        #     print(k, v)

        # print(type(yArray))
        # print('-----------------------')
        # for t in args:
        #     print(t)
        #     print(type(t))

        self._cr.execute('''
                    SELECT *
                    FROM sale_order
                    WHERE name ilike '%''' + str(name) + '''%'
                    LIMIT 1;
                ''')
        query_res = self._cr.fetchall()
        # print(' - '.join([str(res[0]) for res in query_res]))

        return [res for res in query_res]

    @api.onchange('document_reference')
    def set_caps(self):
        if self.document_reference:
            val = str(self.document_reference)
            self.document_reference = val.upper()

    @api.onchange('order_id')
    def _onchange_order_id(self):
        self.set_order(self.order_id.id)

    @api.model
    def set_order(self, order_id):
        # TODO set order
        sale_order = self.env['sale.order'].search([('id', '=', order_id)])
        # action = self.env.ref('sale.order').read()[0]
        # action['context'] = {'id': order_id,}
        # action['context']['form_view_initial_mode'] = 'edit'
        # action['context']['view_no_maturity'] = False
        # action['views'] = [(self.env.ref('sale.order.custom.form').id, 'form')]
        # action['res_id'] = self.copy().id
        # return action
        # vals = self.with_context(active_test=False).copy_data(sale_order[0])[0]
        print(order_id)
        print(sale_order)
        # for r in sale_order:
        #     print('-----------------------')
        #     print(r.order_line)
        #     for rec in self:
        #         rec.order_line = r.order_line or ''
        #         rec.comment_apply = r.comment_apply
        # sale_order1 = sale_order.copy()
        # if sale_order:
        #     # print(type(sale_order))
        #     print('-----------------------')
        #     print(sale_order[0].order_line)
        #     for rec in self:
        #         rec.order_line = sale_order[0].order_line or ()
        #         rec.comment_apply = sale_order[0].comment_apply or ''
        # raise ValidationError(
        #     _('on change'))
        # args = [('id', '=', order_id)]
        # quotations_custom = super(QuotationsCustom, self).search(args)
        default = dict(None or [])
        if sale_order:
            lines = [rec.copy_data()[0] for rec in sale_order[0].order_line.sorted(key='id')]
            default['order_line'] = [(0, 0, line) for line in lines if line]
            for rec in self:
                rec.order_line = default['order_line'] or ()
                rec.comment_apply = sale_order[0].comment_apply or ''

        # return quotations_custom


def attrsetter(attr, value):
    """ Return a function that sets ``attr`` on its argument and returns it. """
    return lambda method: setattr(method, attr, value) or method


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
    ], string='Class Item', default='normal')
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


class QuotationReportHeaderCustom(models.Model):
    _name = "sale.order.reportheader"
    _rec_name = 'name'

    name = fields.Char(string='Report Header')


class SaleCustom(models.Model):
    _name = "sale.custom"

    sale_order_ids = fields.One2many('sale.order', 'sale_custom_id', 'Sale Order', copy=True)
    # custom_attribute_line_ids = fields.One2many('product.custom.template.attribute.line', 'product_id',
    #                                             'Product Attributes', copy=True)
