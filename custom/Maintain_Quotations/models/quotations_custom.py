# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import operator
from datetime import timedelta, time, datetime
from addons.account.models.product import ProductTemplate
from custom.Maintain_Invoice_Remake.models.invoice_customer_custom import rounding, get_tax_method
from odoo.tools.float_utils import float_round, float_compare

import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import re
from odoo.osv import expression
from operator import attrgetter, itemgetter

_logger = logging.getLogger(__name__)


# def get_tax_method(tax_category, tax_unit):
#     # 消費税区分 = ３．非課税 or 消費税区分 is null or 消費税計算区分 is null ==> 税転嫁 = 非課税
#     if (tax_category == 'exempt') or (not tax_category) or (not tax_unit):
#         return 'no_tax'
#     else:
#         # 消費税計算区分 = １．明細単位
#         if tax_unit == 'detail':
#             # 消費税区分 = １．外税 ==> 税転嫁 = 外税／明細
#             if tax_category == 'foreign':
#                 return 'foreign_tax'
#             # 消費税区分 = 2．内税 ==> 税転嫁 = 内税／明細
#             else:
#                 return 'internal_tax'
#         # 消費税計算区分 = ２．伝票単位、３．請求単位 ==> 税転嫁 = 伝票、請求
#         else:
#             return tax_unit


class QuotationsCustom(models.Model):
    _inherit = "sale.order"
    # _rec_name = 'document_no'
    _order = 'document_no'

    def get_order_lines(self):
        return len(self.order_line)

    def _get_next_quotation_no(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'sale.order'), ('number_next', '=', '1000000')])
        next = sequence.get_next_char(sequence.number_next_actual)
        return next


    name = fields.Char(string='Name', default=None)
    shipping_address = fields.Char(string='Shipping Address')
    expected_date = fields.Text(string='Expected Date')
    note = fields.Text(string='Note')
    create_date = fields.Datetime(string='Create Date')
    amount_untaxed = fields.Monetary(string='Amount Untaxed')
    amount_tax = fields.Monetary(string='Amount Tax')
    amount_total = fields.Monetary(string='Amount Total')
    # partner_id = fields.Many2one(string='Partner Order')

    document_no = fields.Char(string='Document No', default=_get_next_quotation_no)
    document_reference = fields.Char(string='Document No Reference')

    expiration_date = fields.Text(string='Expiration Date')
    comment = fields.Text(string='Comment')
    # is_unit_quotations = fields.Boolean(string='Unit Quotations')
    quotation_type = fields.Selection([
        ('unit', 'Unit Quotation'),
        ('normal', 'Normal Quotation')
    ], string='Unit/Normal Quotation', default='normal')
    is_print_date = fields.Boolean(string='Print Date', default=True)
    tax_method = fields.Selection([
        ('foreign_tax', '外税／明細'),
        ('internal_tax', '内税／明細'),
        ('voucher', '伝票'),
        ('invoice', '請求'),
        ('custom_tax', '税調整別途')
    ], string='Tax Method', default='foreign_tax')

    # 消費税端数処理
    customer_tax_rounding = fields.Selection(
        [('round', 'Rounding'), ('roundup', 'Round Up'), ('rounddown', 'Round Down')],
        string='Tax Rounding', default='round')

    quotations_date = fields.Date(string='Quotations Date', default=fields.Date.today())
    order_id = fields.Many2one('sale.order', string='Order', store=False)
    partner_id = fields.Many2one(string='Business Partner')
    related_partner_code = fields.Char('Partner Code')
    partner_name = fields.Char(string='Partner Name')
    partner_name_2 = fields.Char(string='Partner Name 2')
    # minhnt add
    quotation_calendar = fields.Selection([('japan', '和暦'),('origin','西暦')], string='Calendar')
    sales_rep = fields.Many2one('res.users', string='Sales Rep', readonly=True, default=lambda self: self.env.uid,
                                states={'draft': [('readonly', False)]}, )
    related_sales_rep_name = fields.Char('Sales rep name', related='sales_rep.name')
    cb_partner_sales_rep_id = fields.Many2one('hr.employee', string='cbpartner_salesrep_id')
    comment_apply = fields.Text(string='Comment Apply', readonly=True, states={'draft': [('readonly', False)]})
    report_header = fields.Many2one('sale.order.reportheader', string='Report Header')
    # report_header = fields.Selection([
    #     ('quotation', 'Quotation'),
    #     ('invoice', 'Invoice'),
    #     ('sale', 'Sale')
    # ], string='Report Header', readonly=False, default='quotation')
    paperformat_id = fields.Many2one(related='company_id.paperformat_id', string='Paper Format')
    paper_format = fields.Selection([
        ('delivery', '納品書'),('quotation1','見積り１'),('quotation2','見積り2')
    ], string='Pager format', default='delivery')

    # related_product_name = fields.Char(related='order_line.product.product_code_1')
    line_number = fields.Integer(string='明細数', default=get_order_lines, store=False)

    # Reference to account move to copy data to quotation
    refer_invoice_history = fields.Many2one('account.move', store=False)

    @api.onchange('refer_invoice_history')
    def _onchange_refer_invoice_history(self):
        if self.refer_invoice_history:
            data = self.refer_invoice_history

            self.partner_id = data.partner_id
            self.partner_name = data.x_studio_name
            self.name = data.x_bussiness_partner_name_2
            self.document_reference = data.x_studio_document_no
            # self.expected_date = data.expected_date
            self.shipping_address = data.x_studio_address_1 + data.x_studio_address_2 + data.x_studio_address_3
            self.note = data.x_studio_description
            self.expiration_date = data.customer_closing_date
            self.comment = ''
            self.quotations_date = ''
            self.is_print_date = False


            # self.cb_partner_sales_rep_id = data.cb_partner_sales_rep_id
            # self.sales_rep = data.sales_rep
            # self.quotation_type = data.quotation_type
            # self.report_header = data.report_header
            # self.paperformat_id = data.paperformat_id
            # self.paper_format = data.paper_format
            # self.is_print_date = data.is_print_date
            # self.tax_method = data.tax_method
            # self.comment_apply = data.comment_apply

            # default = dict(None or [])
            # lines = [rec.copy_data()[0] for rec in data[0].invoice_line_ids.sorted(key='id')]
            # default['order_line'] = [(0, 0, line) for line in lines if line]
            # for rec in self:
            #     rec.order_line = default['order_line'] or ()

            lines = []
            self.order_line = ()

            for line in data.invoice_line_ids:
                lines.append((0, 0, {
                    'product_id': line.product_id,
                    'product_barcode': line.x_product_barcode,
                    'product_name': line.x_product_name,
                    'product_standard_number': line.invoice_custom_standardnumber,
                    'product_freight_category': line.invoice_custom_FreightCategory,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'product_uom': line.product_uom_id,
                    'line_amount': line.invoice_custom_lineamount,
                    'tax_id': line.tax_ids,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount
                }))

            self.order_line = lines

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                if order.tax_method == 'voucher' and line.product_id.product_tax_category == 'foreign':
                    # total_line_tax = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())
                    line_tax_amount = (line.tax_rate * line.price_unit * line.product_uom_qty) / 100
                    amount_tax += line_tax_amount
                else:
                    amount_tax += line.line_tax_amount

                amount_untaxed += line.line_amount
                # amount_tax += line.line_tax_amount
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.onchange('partner_id')
    def _get_detail_product(self):
        if self.partner_id:
            for rec in self:
                rec.partner_id = self.partner_id or ''
                rec.partner_name = self.partner_id.name or ''
                rec.customer_tax_rounding = self.partner_id.customer_tax_rounding or ''
                rec.cb_partner_sales_rep_id = self.partner_id.customer_agent or ''
                rec.tax_method = get_tax_method(tax_unit=rec.partner_id.customer_tax_unit)

    def get_lines(self):
        records = self.env['sale.order.line'].search([
            ('order_id', 'in', self._ids)
        ]).read()

        for record in records:
            if record['tax_id']:
                self._cr.execute('''
                                    SELECT id, name
                                    FROM account_tax
                                    WHERE id IN %s
                                ''', [tuple(record['tax_id'])])
                query_res = self._cr.fetchall()
                record['tax_id'] = ', '.join([str(res[1]) for res in query_res])

            if record['display_type']:
                record['class_item'] = record['name']
                record['name'] = ''

        return {
            'template': 'order_lines',
            'records': records
        }

    # Check validate, duplicate data
    def _check_data(self, values):
        # check document no.
        if values.get('document_no'):
            sale_order_count = self.env['sale.order'].search_count(
                [('document_no', '=', values.get('document_no'))])
            if sale_order_count > 0:
                raise ValidationError(_('The Document No has already been registered'))

        return True

    @api.model
    def create(self, values):
        # set document_no
        # if not ('document_no' in values):
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

        self._check_data(values)
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
        self._check_data(values)
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

        if sale_order:
            self.document_reference = sale_order.document_reference
            self.name = sale_order.name
            self.partner_id = sale_order.partner_id
            self.partner_name = sale_order.partner_name
            self.cb_partner_sales_rep_id = sale_order.cb_partner_sales_rep_id
            self.shipping_address = sale_order.shipping_address
            self.sales_rep = sale_order.sales_rep
            self.expected_date = sale_order.expected_date
            self.expiration_date = sale_order.expiration_date
            self.note = sale_order.note
            self.comment = sale_order.comment
            self.quotation_type = sale_order.quotation_type
            self.report_header = sale_order.report_header
            self.paperformat_id = sale_order.paperformat_id
            self.paper_format = sale_order.paper_format
            self.is_print_date = sale_order.is_print_date
            self.tax_method = sale_order.tax_method
            self.comment_apply = sale_order.comment_apply

            default = dict(None or [])
            lines = [rec.copy_data()[0] for rec in sale_order[0].order_line.sorted(key='id')]
            default['order_line'] = [(0, 0, line) for line in lines if line]
            for rec in self:
                rec.order_line = default['order_line'] or ()


class QuotationsLinesCustom(models.Model):
    _inherit = "sale.order.line"

    name = fields.Text(string='Description', default=None)
    tax_id = fields.Many2many(string='Taxes')
    tax_rate = fields.Float('Tax Rate', compute='compute_tax_rate')
    product_id = fields.Many2one(string='Product')
    product_uom_qty = fields.Float(string='Product UOM Qty', digits='(12,0)', default=1.0)
    product_uom = fields.Many2one(string='Product UOM')
    price_unit = fields.Float(string='Price Unit')

    class_item = fields.Selection([
        ('通常', '通常'),
        ('返品', '返品'),
        ('値引', '値引'),
        ('消費税', '消費税')
    ], string='Class Item', default='通常')

    product_barcode = fields.Char(string='Product Barcode')
    product_freight_category = fields.Many2one('freight.category.custom', 'Freight Category')
    product_name = fields.Char(string='Product Name')
    product_standard_number = fields.Char(string='Product Standard Number')
    product_list_price = fields.Float(string='Product List Price')
    cost = fields.Float(string='Cost')
    line_amount = fields.Float('Line Amount', compute='compute_line_amount')

    line_tax_amount = fields.Float('Tax Amount', compute='compute_line_tax_amount')

    # Reference to open dialog
    refer_detail_history = fields.Many2one('sale.order.line', store=False)

    @api.onchange('refer_detail_history')
    def _get_detail_history(self):
        if self.refer_detail_history:
            data = self.refer_detail_history

            if not data.display_type:
                self.class_item = data.class_item
                self.product_id = data.product_id
                self.product_name = data.product_name
                self.product_barcode = data.product_barcode
                self.product_freight_category = data.product_freight_category
                self.product_standard_number = data.product_standard_number
                self.product_list_price = data.product_list_price
                self.product_uom_qty = data.product_uom_qty
                self.product_uom = data.product_uom
                self.price_unit = data.price_unit
                self.cost = data.cost
                self.line_amount = data.line_amount
                self.tax_rate = data.tax_rate
                self.line_tax_amount = data.line_tax_amount

            self.name = data.name
            self.display_type = data.display_type

    @api.onchange('product_id')
    def _get_detail_product(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            # if self.product_id:
            #     for rec in self:
            line.product_id = line.product_id or ''
            line.product_name = line.product_id.name or ''
            line.product_barcode = line.product_id.barcode or ''
            line.product_freight_category = line.product_id.product_custom_freight_category or ''
            line.product_standard_number = line.product_id.product_custom_standardnumber or ''

            line.compute_price_unit()
            line.compute_line_amount()
            line.compute_line_tax_amount()

    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes
            line.tax_rate = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())

    @api.depends('tax_id', 'order_id.tax_method', 'order_id.customer_tax_rounding', 'class_item', 'tax_rate')
    def compute_tax_rate(self):
        for line in self:
            line.tax_rate = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'order_id.tax_method',
                 'order_id.customer_tax_rounding', 'class_item', 'tax_rate')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

            if line.class_item in ('通常', '消費税'):
                if line.product_uom_qty < 0:
                    line.product_uom_qty = line.product_uom_qty * (-1)
            else:
                if line.product_uom_qty > 0:
                    line.product_uom_qty = line.product_uom_qty * (-1)

            line.compute_price_unit()
            line.compute_line_amount()
            line.compute_line_tax_amount()

    def compute_price_unit(self):
        for line in self:
            line.product_list_price = line.product_id.standard_price or ''
            line.cost = line.product_id.cost or ''
            # todo set price follow product code
            if line.order_id.tax_method == 'internal_tax':
                line.price_unit = line.product_id.price_include_tax_1 or ''
            elif line.order_id.tax_method in ('voucher', 'invoice'):
                line.price_unit = line.product_id.price_1 or ''
            else:
                line.price_unit = line.product_id.price_no_tax_1 or ''

    def compute_line_amount(self):
        for line in self:
            line.line_amount = self.get_compute_line_amount(line.price_unit, line.discount, line.product_uom_qty,
                                                            line.order_id.customer_tax_rounding)

    def get_compute_line_amount(self, price_unit=0, discount=0, quantity=0, line_rounding='round'):
        result = price_unit * quantity - (discount * price_unit / 100) * quantity
        return rounding(result, 2, line_rounding)

    def compute_line_tax_amount(self):
        for line in self:
            if (line.order_id.tax_method == 'foreign_tax' and line.product_id.product_tax_category != 'exempt') \
                    or line.order_id.tax_method == 'custom_tax':
                # total_line_tax = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())
                line.line_tax_amount = self.get_compute_line_tax_amount(line.line_amount,
                                                                        line.tax_rate,
                                                                        line.order_id.customer_tax_rounding,
                                                                        line.class_item)
            else:
                line.line_tax_amount = 0

    def get_compute_line_tax_amount(self, line_amount, line_taxes, line_rounding, line_type):
        if line_amount != 0:
            return rounding(line_amount * line_taxes / 100, 2, line_rounding)
        else:
            return 0


class QuotationReportHeaderCustom(models.Model):
    _name = "sale.order.reportheader"
    _rec_name = 'name'

    name = fields.Char(string='Report Header')
