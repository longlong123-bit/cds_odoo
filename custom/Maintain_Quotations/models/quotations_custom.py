# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import operator
from datetime import timedelta, time, datetime
from addons.account.models.product import ProductTemplate
from custom.Maintain_Invoice_Remake.models.invoice_customer_custom import rounding, get_tax_method
from odoo.tools.float_utils import float_round, float_compare
import pytz
import logging
import json

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import re
from odoo.osv import expression
from operator import attrgetter, itemgetter

_logger = logging.getLogger(__name__)


class QuotationsCustom(models.Model):
    _inherit = "sale.order"
    _order = "quotations_date desc, document_no desc"
    _rec_name = "display_name"

    def get_default_quotations_date(self):
        _date_now = datetime.now()
        return _date_now.astimezone(pytz.timezone(self.env.user.tz))

    def _get_domain_sales_rep(self):
        cr = self.env.cr
        user_ids = []
        cr.execute(
            "SELECT id FROM res_groups WHERE (name='User: Only Customer Master And Product Master in New Master Menu' OR name='ユーザー：マスタ管理に得意先マスタと商品マスタがあるだけ') AND category_id=55")
        groups = cr.fetchall()
        for group_id in groups:
            cr.execute("SELECT uid FROM res_groups_users_rel WHERE gid = " + str(group_id[0]))
            user_uid = cr.fetchall()
            user_ids.append(user_uid[0][0])

        # Get users in group system
        res_users_group_system_ids = self.env['res.users'].search([('active', '=', True)]).filtered(
            lambda l: l.has_group('base.group_system'))

        domain = [('id', 'not in', user_ids),
                  ('id', 'not in', res_users_group_system_ids.ids)]
        return domain

    def get_order_lines(self):
        return len(self.order_line)

    def _get_next_quotation_no(self):
        sequence = self.env['ir.sequence'].search(
            [('code', '=', 'sale.order'), ('prefix', '=', 'ARQ-')])
        next = sequence.get_next_char(sequence.number_next_actual)
        return next

    display_name = fields.Char(string='display_name', default='修正')
    name = fields.Char(string='Name', default=None)
    quotation_name = fields.Char(string='Name', default=None)
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

    quotations_date = fields.Date(string='Quotations Date', default=get_default_quotations_date)
    order_id = fields.Many2one('sale.order', string='Order', store=False)
    partner_id = fields.Many2one('res.partner', string='Business Partner')
    related_partner_code = fields.Char('Partner Code', related='partner_id.customer_code')
    partner_name = fields.Char(string='Partner Name')
    partner_name_2 = fields.Char(string='Partner Name 2')
    # minhnt add
    quotation_calendar = fields.Selection([('japan', '和暦'), ('origin', '西暦')], string='Calendar', default='japan')
    sales_rep = fields.Many2one('res.users', string='Sales Rep', readonly=True, default=lambda self: self.env.uid,
                                domain=_get_domain_sales_rep,
                                states={'draft': [('readonly', False)]}, )
    related_sales_rep_name = fields.Char('Sales rep name', related='sales_rep.name')
    cb_partner_sales_rep_id = fields.Many2one('hr.employee', string='cbpartner_salesrep_id')
    comment_apply = fields.Text(string='Comment Apply', readonly=True, states={'draft': [('readonly', False)]})

    def _default_report_header(self):
        # TH - Change default
        reportheader_temp = []
        default = self.env['sale.order.reportheader'].search([('name', 'ilike', '見')])
        if not default:
            return ''
        else:
            for report in default:
                report_replace = report.name.replace(' ', '').replace('　', '')
                if report_replace == '見積書':
                    if report.name == '見　積　書':
                        return report.id
                    reportheader_temp.append(report.id)
            if reportheader_temp:
                return max(reportheader_temp)
            else:
                return ''

    report_header = fields.Many2one('sale.order.reportheader', string='Report Header', default=_default_report_header)
    # report_header = fields.Selection([
    #     ('quotation', 'Quotation'),
    #     ('invoice', 'Invoice'),
    #     ('sale', 'Sale')
    # ], string='Report Header', readonly=False, default='quotation')
    paperformat_id = fields.Many2one(related='company_id.paperformat_id', string='Paper Format')
    paper_format = fields.Selection([
        ('delivery', '納品書'), ('quotation', '見積書')
    ], string='Pager format', default='quotation')

    # related_product_name = fields.Char(related='order_line.product.product_code_1')
    line_number = fields.Integer(string='明細数', default=get_order_lines, store=False)

    # Reference to account move to copy data to quotation
    refer_invoice_history = fields.Many2one('account.move', store=False)

    # flag history button
    flag_history = fields.Integer(string='flag_history', default=0, compute='_check_flag_history')

    # Check flag_history
    # @api.constrains('partner_id')
    # def get_flag(self):
    #     for rec in self:
    #         rec.flag_history = 0

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.order_id.partner_name_2:
            self.partner_name_2 = self.order_id.partner_name_2
        else:
            self.partner_name_2 = self.partner_id.customer_name_2

    @api.onchange('partner_id', 'partner_name', 'quotation_name', 'document_reference', 'expected_date',
                  'shipping_address', 'note', 'expiration_date', 'comment', 'comment_apply', 'cb_partner_sales_rep_id',
                  'partner_name_2', 'quotations_date', 'quotation_type', 'report_header', 'tax_method', 'sales_rep',
                  'amount_untaxed')
    def change_tax_rounding(self):
        self.ensure_one()
        self.customer_tax_rounding = self.partner_id.customer_tax_rounding

    @api.onchange('partner_id', 'partner_name', 'quotation_name', 'document_reference', 'expected_date',
                  'shipping_address', 'note', 'expiration_date', 'comment', 'comment_apply', 'cb_partner_sales_rep_id',
                  'partner_name_2')
    def _check_flag_history(self):
        for rec in self:
            if rec.partner_name or rec.partner_id or rec.quotation_name or rec.document_reference or rec.expected_date \
                    or rec.shipping_address or rec.note or rec.expiration_date or rec.comment or rec.comment_apply \
                    or rec.cb_partner_sales_rep_id or rec.partner_name_2:
                rec.flag_history = 1
            else:
                rec.flag_history = 0

    @api.onchange('refer_invoice_history')
    def _onchange_refer_invoice_history(self):
        for rec in self:
            if rec.refer_invoice_history:
                rec.flag_history = 1
        if self.refer_invoice_history:
            data = self.refer_invoice_history

            self.partner_id = data.partner_id
            self.partner_name = data.x_studio_name
            self.name = data.x_bussiness_partner_name_2
            self.document_reference = data.x_studio_document_no
            # self.expected_date = data.expected_date
            self.shipping_address = str(data.x_studio_address_1 or '') + str(data.x_studio_address_2 or '') + str(
                data.x_studio_address_3 or '')
            self.note = data.x_studio_summary
            self.expiration_date = data.customer_closing_date
            self.comment = ''
            self.quotations_date = datetime.now().astimezone(pytz.timezone(self.env.user.tz)) or ''
            self.is_print_date = False

            # self.cb_partner_sales_rep_id = data.cb_partner_sales_rep_id
            # self.sales_rep = data.sales_rep
            # self.quotation_type = data.quotation_type
            # self.report_header = data.report_header
            # self.paperformat_id = data.paperformat_id
            # self.paper_format = data.paper_format
            # self.is_print_date = data.is_print_date
            self.tax_method = data.x_voucher_tax_transfer
            # self.comment_apply = data.comment_apply

            # default = dict(None or [])
            # lines = [rec.copy_data()[0] for rec in data[0].invoice_line_ids.sorted(key='id')]
            # default['order_line'] = [(0, 0, line) for line in lines if line]
            # for rec in self:
            #     rec.order_line = default['order_line'] or ()

            lines = []
            # self.order_line = ()

            for line in data.invoice_line_ids.sorted(key=lambda i: i.invoice_custom_line_no):
                lines.append((0, 0, {
                    'product_id': line.product_id,
                    'product_code': line.product_code,
                    'product_barcode': line.product_barcode,
                    'product_name': line.product_name,
                    'product_name2': line.product_name2,
                    'product_uom_id': line.product_uom_id,
                    'product_standard_number': line.invoice_custom_standardnumber,
                    'product_maker_name': line.product_maker_name,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'line_amount': line.invoice_custom_lineamount,
                    'tax_id': line.tax_ids,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount,
                    'description': line.invoice_custom_Description,
                    'price_include_tax': line.price_include_tax,
                    'price_no_tax': line.price_no_tax,
                    'quotation_custom_line_no': line.invoice_custom_line_no
                }))

            self.order_line = lines

    @api.constrains('quotations_date', 'order_line', 'partner_name', 'document_no')
    def _change_date_invoiced(self):
        for line in self.order_line:
            line.quotation_date = self.quotations_date
            line.partner_id = self.partner_id
            line.document_no = self.document_no
            line.customer_name = self.partner_name

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                if line.class_item != 'サンプル':
                    if order.tax_method != 'custom_tax':
                        if order.tax_method == 'voucher' and line.product_id.product_tax_category == 'foreign':
                            # total_line_tax = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())
                            line_tax_amount = (line.tax_rate * line.price_unit * line.product_uom_qty) / 100
                            amount_tax += line_tax_amount
                        else:
                            amount_tax += line.line_tax_amount
                    else:
                        amount_tax = order.amount_tax

                    amount_untaxed += line.line_amount
                # amount_tax += line.line_tax_amount

            if order.tax_method == 'voucher':
                amount_tax = rounding(amount_tax, 0, order.customer_tax_rounding)

            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.onchange('amount_tax')
    def _onchange_amount_tax(self):
        for order in self:
            amount_untaxed = 0.0
            for line in order.order_line:
                if line.class_item != 'サンプル':
                    amount_untaxed += line.line_amount
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_total': amount_untaxed + self.amount_tax,
            })

    @api.onchange('partner_id')
    def _get_detail_product(self):
        if self.partner_id:
            for rec in self:
                rec.partner_id = self.partner_id or ''
                rec.partner_name = self.partner_id.name or ''
                rec.customer_tax_rounding = \
                    self.partner_id.customer_tax_rounding or ''
                rec.cb_partner_sales_rep_id = \
                    self.partner_id.customer_agent or ''
                if not rec.order_id and not rec.refer_invoice_history:
                    rec.tax_method = get_tax_method(
                        tax_unit=rec.partner_id.customer_tax_unit)

    def get_lines(self):
        records = self.env['sale.order.line'].search([
            ('order_id', 'in', self._ids)
        ], order='quotation_custom_line_no').read()

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
        if not values.get('order_line', []):
            raise UserError(_("You need to add a line before save."))
        self._cr.execute('''
                        SELECT document_no
                        FROM sale_order
                        WHERE SUBSTRING(document_no, 5) ~ '^[0-9\.]+$';
                    ''')
        query_res = self._cr.fetchall()

        # generate new document no. by sequence
        if values.get('document_no'):
            seq = values['document_no']
        else:
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
        for rec in self:
            if rec.order_id:
                rec.flag_history = 1

        self.set_order(self.order_id.id)

    @api.model
    def set_order(self, order_id):
        # TODO set order
        sale_order = self.env['sale.order'].browse(order_id)

        if sale_order:
            self.document_reference = sale_order.document_reference
            self.name = sale_order.name
            self.partner_id = sale_order.partner_id
            self.partner_name = sale_order.partner_name
            self.quotation_name = sale_order.quotation_name
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
            # self.order_line = ()

            # default = dict(None or [])
            # lines = [rec.copy_data()[0] for rec in sale_order[0].order_line.sorted(key='id')]
            order_lines = []
            for line in sale_order[0].order_line.sorted(key='quotation_custom_line_no'):
                copied_data = line.copy_data()[0]
                copied_data['quotation_custom_line_no'] = line.quotation_custom_line_no
                order_lines += [[0, 0, copied_data]]
            # default['order_line'] = [(0, 0, line) for line in lines if line]
            self.order_line = order_lines

    jp_calendar = fields.Char('jp_calendar', compute='set_jp_calendar')

    def set_jp_calendar(self):
        ERA_JP = (
            ("M", "明治"),
            ("T", "大正"),
            ("S", "昭和"),
            ("H", "平成"),
            ("R", "令和"),
        )
        for record in self:
            if record.quotations_date < datetime.strptime('1912-30-7', '%Y-%d-%m').date():
                era_year = record.quotations_date.year - 1867
                era, era_ch = ERA_JP[0]
            elif record.quotations_date < datetime.strptime('1926-25-12', '%Y-%d-%m').date():
                era_year = record.quotations_date.year - 1911
                era, era_ch = ERA_JP[1]
            elif record.quotations_date < datetime.strptime('1989-8-1', '%Y-%d-%m').date():
                era_year = record.quotations_date.year - 1925
                era, era_ch = ERA_JP[2]
            elif record.quotations_date < datetime.strptime('2019-1-5', '%Y-%d-%m').date():
                era_year = record.quotations_date.year - 1988
                era, era_ch = ERA_JP[3]
            else:
                era_year = record.quotations_date.year - 2018
                era, era_ch = ERA_JP[4]
            jp_c = str(era_ch) + str(era_year) + '年' + str(record.quotations_date.month) + '月' + str(
                record.quotations_date.day) + '日'
            record.jp_calendar = jp_c

    copy_history_item = fields.Char(default="")
    copy_history_from = fields.Char(default="")

    @api.onchange('copy_history_item')
    def copy_from_history(self):
        if not self.copy_history_item:
            return
        products = []
        invoice_line_ids = []
        if self.copy_history_from == 'sale.order.line' and self.copy_history_item:
            products = self.env["sale.order.line"].search([('id', 'in', self.copy_history_item.split(','))])
            for line in products:
                self.order_line = [(0, False, {
                    'class_item': line.class_item,
                    'product_id': line.product_id,
                    'product_code': line.product_code,
                    'product_barcode': line.product_barcode,
                    'product_name': line.product_name,
                    'product_name2': line.product_name2,
                    'product_standard_number': line.product_standard_number,
                    'product_maker_name': line.product_maker_name,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'product_uom_id': line.product_uom_id,
                    'line_amount': line.line_amount,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount,
                    'price_include_tax': line.price_include_tax,
                    'price_no_tax': line.price_no_tax,
                    'description': line.description,
                    'quotation_custom_line_no': len(self.order_line) + 1,
                    'copy_history_flag': True,
                })]
        elif self.copy_history_from == 'account.move.line' and self.copy_history_item:
            products = self.env["account.move.line"].search([('id', 'in', self.copy_history_item.split(','))])
            for line in products:
                self.order_line = [(0, False, {
                    'class_item': line.x_invoicelinetype,
                    'product_id': line.product_id,
                    'product_code': line.product_code,
                    'product_barcode': line.product_barcode,
                    'product_name': line.product_name,
                    'product_name2': line.product_name2,
                    'product_standard_number': line.invoice_custom_standardnumber,
                    'product_maker_name': line.product_maker_name,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'product_uom_id': line.product_uom_id,
                    'line_amount': line.invoice_custom_lineamount,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount,
                    'price_include_tax': line.price_include_tax,
                    'price_no_tax': line.price_no_tax,
                    'description': line.invoice_custom_Description,
                    'quotation_custom_line_no': len(self.order_line) + 1,
                    'copy_history_flag': True,
                })]
        elif self.copy_history_from == 'product.product':
            product_ids = [int(product_id) for product_id in
                           self.copy_history_item.split(',')]
            products = self.env["product.product"].browse(product_ids)
            line_vals = []
            for i, product in enumerate(products, 1):
                line_vals += \
                    [(0, False,
                      {'product_id': product.id,
                       'product_code': product.product_code,
                       'product_barcode': product.barcode,
                       'product_name': product.name,
                       'product_name2': product.product_custom_goodsnamef,
                       'product_standard_number':
                           product.product_custom_standardnumber,
                       'product_maker_name': product.product_maker_name,
                       'product_uom': product.uom_id.id,
                       'product_uom_id': product.product_uom_custom,
                       'cost': product.cost,
                       'product_standard_price': product.standard_price or 0.00,
                       'tax_rate': product.product_tax_rate,
                       'quotation_custom_line_no': len(self.order_line) + i})]
            self.order_line = line_vals
            for line in self.order_line:
                if line.product_code:
                    line._onchange_product_code()
                elif line.product_barcode:
                    line._onchange_product_barcode()
                # line.compute_price_unit()
        elif self.copy_history_from == 'duplicated':
            self.order_line = [(0, False,{
                'class_item': self.order_line[int(self.copy_history_item)].class_item,
                'product_id': self.order_line[int(self.copy_history_item)].product_id.id,
                'product_code': self.order_line[int(self.copy_history_item)].product_code,
                'product_barcode': self.order_line[int(self.copy_history_item)].product_barcode,
                'product_name': self.order_line[int(self.copy_history_item)].product_name,
                'product_name2': self.order_line[int(self.copy_history_item)].product_name2,
                'product_standard_number': self.order_line[int(self.copy_history_item)].product_standard_number,
                'product_maker_name': self.order_line[int(self.copy_history_item)].product_maker_name,
                'product_uom_qty': self.order_line[int(self.copy_history_item)].product_uom_qty,
                'price_unit': self.order_line[int(self.copy_history_item)].price_unit,
                'product_uom_id': self.order_line[int(self.copy_history_item)].product_uom_id,
                'line_amount': self.order_line[int(self.copy_history_item)].line_amount,
                'tax_rate': self.order_line[int(self.copy_history_item)].tax_rate,
                'line_tax_amount': self.order_line[int(self.copy_history_item)].line_tax_amount,
                'price_include_tax': self.order_line[int(self.copy_history_item)].price_include_tax,
                'price_no_tax': self.order_line[int(self.copy_history_item)].price_no_tax,
                'description': self.order_line[int(self.copy_history_item)].description,
                'quotation_custom_line_no': len(self.order_line) + 1,
                'copy_history_flag': self.order_line[int(self.copy_history_item)].copy_history_flag,
            })]
        self.copy_history_item = ''

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        odoo/models.py
        """

        ctx = self._context.copy()
        domain = []
        # print('aaaaaaaa', ctx.get('have_advance_search'))
        # if ctx.get('view_name') == 'main_sale_order':
        if ctx.get('have_advance_search'):
            check = 0
            arr = ["quotation_name", "related_partner_code", "partner_name", "related_sales_rep_name"]
            for se in args:
                if se[0] == '&':
                    continue
                if se[0] == 'search_category' and se[2] == 'equal':
                    check = 1
                if check == 1 and se[0] in arr:
                    se[1] = '=ilike'
                if se[0] != 'search_category':
                    domain += [se]
                #TH - custom domain
                if se[0] == 'document_no':
                    string_middle = ''
                    if len(se[2]) < 7:
                        for i in range(6 - len(se[2])):
                            string_middle += '0'
                        string_middle = '1' + string_middle
                    if len(se[2]) < 11:
                        se[2] = ''.join(["ARQ-", string_middle, se[2]])
                #TH - done
            args = domain
        res = super(QuotationsCustom, self).search(args, offset=offset, limit=limit, order=order, count=count)
        # if ctx.get('view_name') == 'confirm_sale_order':
        #     check = 0
        #     for se in args:
        #         if se[0] == '&':
        #             continue
        #         # if se[0] == 'search_category' and se[2] == 'equal':
        #         #     check = 1
        #         # arr = ["related_partner_code", "partner_name", "related_sales_rep_name"]
        #         # if check == 1 and se[0] in arr:
        #         #     se[1] = '=ilike'
        #         if se[0] != 'search_category':
        #             domain += [se]
        #     args = domain
        # record = super(QuotationsCustom, self).search(args, offset=offset, limit=limit, order=order, count=count)

        # else:
        #     res = self._search(args, offset=offset, limit=limit, order=order, count=count)
        return res


class QuotationsLinesCustom(models.Model):
    _inherit = "sale.order.line"
    _order = "quotation_custom_line_no asc"

    name = fields.Text(string='Description', default=None)
    tax_id = fields.Many2many(string='Taxes')
    # tax_rate = fields.Float('Tax Rate', compute='compute_tax_rate')
    tax_rate = fields.Float('Tax Rate')
    product_id = fields.Many2one(string='Product')
    product_uom_qty = fields.Float(string='Product UOM Qty', digits=(12, 0), default=1.0)
    product_uom = fields.Many2one(string='Product UOM')
    price_unit = fields.Float(string='Price Unit', digits='Product Price', compute="compute_price_unit", store="True")
    description = fields.Text(string='Description')

    partner_id = fields.Many2one('res.partner', string='Business Partner')
    customer_name = fields.Char(string="Customer Name")
    quotation_date = fields.Date(string='Quotation Date')
    document_no = fields.Char(string='Document No')

    class_item = fields.Selection([
        ('通常', '通常'),
        ('返品', '返品'),
        ('値引', '値引'),
        ('サンプル', 'サンプル')
    ], string='Class Item', default='通常')

    product_code = fields.Char(string='Product Code')
    product_barcode = fields.Char(string='Product Barcode')
    product_maker_name = fields.Char(string='Freight Category')
    product_name = fields.Text(string='Product Name')
    product_name2 = fields.Text(string='Product Name 2')
    product_standard_number = fields.Char(string='Product Standard Number')
    product_standard_price = fields.Float(string='Product List Price')
    cost = fields.Float(string='Cost')
    line_amount = fields.Float('Line Amount', compute='compute_line_amount')

    line_tax_amount = fields.Float('Tax Amount', compute='compute_line_tax_amount')

    # Reference to open dialog
    refer_detail_history = fields.Many2one('sale.order.line', store=False)

    price_no_tax = fields.Float('Price No Tax')
    price_include_tax = fields.Float('Price Include Tax')
    product_tax_category = fields.Selection(
        related="product_id.product_tax_category"
    )

    copy_history_flag = fields.Boolean(default=False, store=False)

    @api.onchange('quotation_custom_line_no', 'class_item', 'product_code', 'product_barcode', 'product_maker_name',
                  'product_name', 'product_standard_number', 'product_uom_qty', 'product_uom_id', 'price_unit',
                  'tax_rate')
    def change_tax_rounding(self):
        self.ensure_one()
        self.order_id.customer_tax_rounding = self.order_id.partner_id.customer_tax_rounding

    def price_of_recruitment_select(self, rate=0, recruitment_price_select=None, price_applied=0):
        if recruitment_price_select:
            product_price_ids = self.env['product.product'].search([('barcode', '=', self.product_barcode)])
            if recruitment_price_select == 'price_1':
                price = product_price_ids.price_1 * rate / 100
            elif recruitment_price_select == 'standard_price':
                price = product_price_ids.standard_price * rate / 100
        else:
            price = price_applied
        return price

    def set_country_state_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                               product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                               maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                               industry_code=None, country_state_code=None, date=datetime.today()):
        country_state_code_ids = self.env['master.price.list'].search([
            ('country_state_code_id', '=', country_state_code),
            ('industry_code_id', '=', industry_code),
            ('supplier_group_code_id', '=', supplier_group_code),
            ('customer_code_bill', '=', customer_code_bill),
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(country_state_code_ids):
            if len(country_state_code_ids) > 1:
                for i in country_state_code_ids:
                    price = self.price_of_recruitment_select(i.rate,
                                                             i.recruitment_price_select,
                                                             i.price_applied)
            else:
                price = self.price_of_recruitment_select(country_state_code_ids.rate,
                                                         country_state_code_ids.recruitment_price_select,
                                                         country_state_code_ids.price_applied)
        else:
            country_state_code_id_none = self.env['master.price.list'].search([
                ('country_state_code_id', '=', None),
                ('industry_code_id', '=', industry_code),
                ('supplier_group_code_id', '=', supplier_group_code),
                ('customer_code_bill', '=', customer_code_bill),
                ('customer_code', '=', customer_code),
                ('maker_code', '=', maker),
                ('product_class_code_lv1_id', '=', product_class_code_lv1),
                ('product_class_code_lv2_id', '=', product_class_code_lv2),
                ('product_class_code_lv3_id', '=', product_class_code_lv3),
                ('product_class_code_lv4_id', '=', product_class_code_lv4),
                ('jan_code', '=', jan_code),
                ('product_code', '=', product_code),
                ('date_applied', '<=', date)]).sorted('date_applied')
            if len(country_state_code_id_none):
                if len(country_state_code_id_none) > 1:
                    for i in country_state_code_id_none:
                        price = self.price_of_recruitment_select(i.rate, i.recruitment_price_select, i.price_applied)
                else:
                    price = self.price_of_recruitment_select(country_state_code_id_none.rate,
                                                             country_state_code_id_none.recruitment_price_select,
                                                             country_state_code_id_none.price_applied)
            else:
                product_price_ids = self.env['product.product'].search([('barcode', '=', self.product_barcode)])
                price = product_price_ids.price_1
        return price

    def set_industry_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                          product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                          maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                          industry_code=None, country_state_code=None, date=datetime.today()):
        industry_code_ids = self.env['master.price.list'].search([
            ('industry_code_id', '=', industry_code),
            ('supplier_group_code_id', '=', supplier_group_code),
            ('customer_code_bill', '=', customer_code_bill),
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(industry_code_ids):
            if len(industry_code_ids) > 1:
                price = self.set_country_state_code(product_code, jan_code, product_class_code_lv4,
                                                    product_class_code_lv3, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(industry_code_ids.rate,
                                                         industry_code_ids.recruitment_price_select,
                                                         industry_code_ids.price_applied)
        else:
            price = self.set_country_state_code(product_code, jan_code, product_class_code_lv4, product_class_code_lv3,
                                                product_class_code_lv2, product_class_code_lv1, maker, None, None, None,
                                                None, country_state_code, date)
        return price

    def set_supplier_group_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                                maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                                industry_code=None, country_state_code=None, date=datetime.today()):
        supplier_group_code_ids = self.env['master.price.list'].search([
            ('supplier_group_code_id', '=', supplier_group_code),
            ('customer_code_bill', '=', customer_code_bill),
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(supplier_group_code_ids):
            if len(supplier_group_code_ids) > 1:
                price = self.set_industry_code(product_code, jan_code, product_class_code_lv4, product_class_code_lv3,
                                               product_class_code_lv2, product_class_code_lv1, maker, customer_code,
                                               customer_code_bill, supplier_group_code, industry_code,
                                               country_state_code, date)
            else:
                price = self.price_of_recruitment_select(supplier_group_code_ids.rate,
                                                         supplier_group_code_ids.recruitment_price_select,
                                                         supplier_group_code_ids.price_applied)
        else:
            price = self.set_industry_code(product_code, jan_code, product_class_code_lv4, product_class_code_lv3,
                                           product_class_code_lv2, product_class_code_lv1, maker, None, None, None,
                                           industry_code, country_state_code, date)
        return price

    def set_customer_code_bill(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                               product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                               maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                               industry_code=None, country_state_code=None, date=datetime.today()):
        customer_code_bill_ids = self.env['master.price.list'].search([
            ('customer_code_bill', '=', customer_code_bill),
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(customer_code_bill_ids):
            if len(customer_code_bill_ids) > 1:
                price = self.set_supplier_group_code(product_code, jan_code, product_class_code_lv4,
                                                     product_class_code_lv3, product_class_code_lv2,
                                                     product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                     supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(customer_code_bill_ids.rate,
                                                         customer_code_bill_ids.recruitment_price_select,
                                                         customer_code_bill_ids.price_applied)
        else:
            price = self.set_supplier_group_code(product_code, jan_code, product_class_code_lv4,
                                                 product_class_code_lv3, product_class_code_lv2,
                                                 product_class_code_lv1, maker, None, None,
                                                 supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_customer_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                          product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                          maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                          industry_code=None, country_state_code=None, date=datetime.today()):
        customer_code_ids = self.env['master.price.list'].search([
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(customer_code_ids):
            if len(customer_code_ids) > 1:
                price = self.set_customer_code_bill(product_code, jan_code, product_class_code_lv4,
                                                    product_class_code_lv3, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(customer_code_ids.rate,
                                                         customer_code_ids.recruitment_price_select,
                                                         customer_code_ids.price_applied)
        else:
            price = self.set_customer_code_bill(product_code, jan_code, product_class_code_lv4,
                                                product_class_code_lv3, product_class_code_lv2,
                                                product_class_code_lv1, maker, None, customer_code_bill,
                                                supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_maker(self, product_code=None, jan_code=None, product_class_code_lv4=None, product_class_code_lv3=None,
                  product_class_code_lv2=None, product_class_code_lv1=None, maker=None, customer_code=None,
                  customer_code_bill=None, supplier_group_code=None, industry_code=None, country_state_code=None, date=datetime.today()):
        maker_ids = self.env['master.price.list'].search([('maker_code', '=', maker),
                                                          ('product_class_code_lv1_id', '=', product_class_code_lv1),
                                                          ('product_class_code_lv2_id', '=', product_class_code_lv2),
                                                          ('product_class_code_lv3_id', '=', product_class_code_lv3),
                                                          ('product_class_code_lv4_id', '=', product_class_code_lv4),
                                                          ('jan_code', '=', jan_code),
                                                          ('product_code', '=', product_code),
                                                          ('date_applied', '<=', date)]).sorted('date_applied')
        if len(maker_ids):
            if len(maker_ids) > 1:
                price = self.set_customer_code(product_code, jan_code, product_class_code_lv4,
                                               product_class_code_lv3, product_class_code_lv2,
                                               product_class_code_lv1, maker, customer_code, customer_code_bill,
                                               supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(maker_ids.rate,
                                                         maker_ids.recruitment_price_select,
                                                         maker_ids.price_applied)
        else:
            product_price_ids = self.env['product.product'].search([('barcode', '=', self.product_barcode)])
            if product_price_ids.price_1:
                price = product_price_ids.price_1
            else:
                price = product_price_ids.standard_price
        return price

    def set_product_class_code_lv1(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                   product_class_code_lv3=None, product_class_code_lv2=None,
                                   product_class_code_lv1=None, maker=None, customer_code=None, customer_code_bill=None,
                                   supplier_group_code=None, industry_code=None, country_state_code=None, date=datetime.today()):
        product_class_code_lv1_ids = self.env['master.price.list'].search([
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_class_code_lv1_ids):
            if len(product_class_code_lv1_ids) > 1:
                price = self.set_maker(product_code, jan_code, product_class_code_lv4,
                                       product_class_code_lv3, product_class_code_lv2,
                                       product_class_code_lv1, maker, customer_code,
                                       customer_code_bill,
                                       supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_class_code_lv1_ids.rate,
                                                         product_class_code_lv1_ids.recruitment_price_select,
                                                         product_class_code_lv1_ids.price_applied)
        else:
            price = self.set_maker(None, None, None, None, None, None, maker, customer_code, customer_code_bill,
                                   supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_product_class_code_lv2(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                   product_class_code_lv3=None, product_class_code_lv2=None,
                                   product_class_code_lv1=None, maker=None, customer_code=None, customer_code_bill=None,
                                   supplier_group_code=None, industry_code=None, country_state_code=None, date=datetime.today()):
        product_class_code_lv2_ids = self.env['master.price.list'].search([
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_class_code_lv2_ids):
            if len(product_class_code_lv2_ids) > 1:
                price = self.set_product_class_code_lv1(product_code, jan_code, product_class_code_lv4,
                                                        product_class_code_lv3, product_class_code_lv2,
                                                        product_class_code_lv1, maker, customer_code,
                                                        customer_code_bill,
                                                        supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_class_code_lv2_ids.rate,
                                                         product_class_code_lv2_ids.recruitment_price_select,
                                                         product_class_code_lv2_ids.price_applied)
        else:
            price = self.set_product_class_code_lv1(None, None, None, None, None,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_product_class_code_lv3(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                   product_class_code_lv3=None, product_class_code_lv2=None,
                                   product_class_code_lv1=None, maker=None, customer_code=None, customer_code_bill=None,
                                   supplier_group_code=None, industry_code=None, country_state_code=None, date=datetime.today()):
        product_class_code_lv3_ids = self.env['master.price.list'].search([
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_class_code_lv3_ids):
            if len(product_class_code_lv3_ids) > 1:
                price = self.set_product_class_code_lv2(product_code, jan_code, product_class_code_lv4,
                                                        product_class_code_lv3, product_class_code_lv2,
                                                        product_class_code_lv1, maker, customer_code,
                                                        customer_code_bill,
                                                        supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_class_code_lv3_ids.rate,
                                                         product_class_code_lv3_ids.recruitment_price_select,
                                                         product_class_code_lv3_ids.price_applied)
        else:
            price = self.set_product_class_code_lv2(None, None, None,
                                                    None, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_product_class_code_lv4(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                   product_class_code_lv3=None, product_class_code_lv2=None,
                                   product_class_code_lv1=None, maker=None, customer_code=None, customer_code_bill=None,
                                   supplier_group_code=None, industry_code=None, country_state_code=None, date=datetime.today()):
        product_class_code_lv4_ids = self.env['master.price.list'].search([
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_class_code_lv4_ids):
            if len(product_class_code_lv4_ids) > 1:
                price = self.set_product_class_code_lv3(product_code, jan_code, product_class_code_lv4,
                                                        product_class_code_lv3, product_class_code_lv2,
                                                        product_class_code_lv1, maker, customer_code,
                                                        customer_code_bill,
                                                        supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_class_code_lv4_ids.rate,
                                                         product_class_code_lv4_ids.recruitment_price_select,
                                                         product_class_code_lv4_ids.price_applied)
        else:
            price = self.set_product_class_code_lv3(None, None, None,
                                                    product_class_code_lv3, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_price_by_jan_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                              product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                              maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                              industry_code=None, country_state_code=None, date=datetime.today()):
        jan_ids = self.env['master.price.list'].search([
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(jan_ids):
            if len(jan_ids) > 1:
                price = self.set_product_class_code_lv4(product_code, jan_code, product_class_code_lv4,
                                                        product_class_code_lv3, product_class_code_lv2,
                                                        product_class_code_lv1, maker, customer_code,
                                                        customer_code_bill,
                                                        supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(jan_ids.rate,
                                                         jan_ids.recruitment_price_select,
                                                         jan_ids.price_applied)
        else:
            price = self.set_product_class_code_lv4(None, None, product_class_code_lv4,
                                                    product_class_code_lv3, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_price_product_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                               product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                               maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                               industry_code=None, country_state_code=None, date=datetime.today()):
        product_code_ids = self.env['master.price.list'].search([('product_code', '=', product_code), ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_code_ids):
            if len(product_code_ids) > 1:
                price = self.set_price_by_jan_code(product_code, jan_code, product_class_code_lv4,
                                                   product_class_code_lv3, product_class_code_lv2,
                                                   product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                   supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_code_ids.rate,
                                                         product_code_ids.recruitment_price_select,
                                                         product_code_ids.price_applied)
        else:
            price = self.set_price_by_jan_code(None, jan_code, product_class_code_lv4, product_class_code_lv3,
                                               product_class_code_lv2, product_class_code_lv1, maker, customer_code,
                                               customer_code_bill, supplier_group_code, industry_code,
                                               country_state_code, date)
        return price

    def _get_default_line_no(self):
        context = dict(self._context or {})
        line_ids = context.get('default_line_ids')
        order_id = context.get('default_order_id')
        # max1 = 0

        list_line = []
        if order_id:
            list_line = self.env["sale.order.line"].search([("order_id.id", "=", order_id)])

        # get all line in db and state draf
        list_final = {}
        if list_line is not None:
            for l_db in list_line:
                list_final[l_db.id] = l_db.quotation_custom_line_no
            if line_ids is not None:
                for l_v in line_ids:
                    # check state (delete,update,new,no change)
                    # 0: new
                    # 1: update
                    # 2: delete
                    # 4: no change
                    if l_v[0] == 0:
                        list_final[l_v[1]] = l_v[2]['quotation_custom_line_no']
                    if l_v[0] == 1 and 'quotation_custom_line_no' in l_v[2]:
                        list_final[l_v[1]] = l_v[2]['quotation_custom_line_no']
                    if l_v[0] == 2:
                        list_final[l_v[1]] = 0
        max = 0
        for id in list_final:
            if max < list_final[id]:
                max = list_final[id]
        return max + 1

    quotation_custom_line_no = fields.Integer('Line No', default=_get_default_line_no)
    product_uom_id = fields.Char(string='UoM')
    changed_fields = []

    @api.onchange('product_code')
    def _onchange_product_code(self):
        if 'product_code' not in self.changed_fields:

            if self.product_code:
                product = self.env['product.product'].search([
                    '|', '|', '|', '|', '|',
                    ['product_code_1', '=', self.product_code],
                    ['product_code_2', '=', self.product_code],
                    ['product_code_3', '=', self.product_code],
                    ['product_code_4', '=', self.product_code],
                    ['product_code_5', '=', self.product_code],
                    ['product_code_6', '=', self.product_code]
                ])
                if len(product) == 1:
                    self.changed_fields.append('product_barcode')
                    self.product_id = product.id
                    self.product_barcode = product.barcode

                    setting_price = "1"
                    if self.product_code == product.product_code_2:
                        setting_price = "2"
                    elif self.product_code == product.product_code_3:
                        setting_price = "3"
                    elif self.product_code == product.product_code_4:
                        setting_price = "4"
                    elif self.product_code == product.product_code_5:
                        setting_price = "5"
                    elif self.product_code == product.product_code_6:
                        setting_price = "6"
                    if product.product_tax_category == 'exempt':
                        self.price_include_tax = self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date)
                    elif product.product_tax_category == 'foreign':
                        self.price_include_tax = (product.product_tax_rate / 100 + 1) * self.set_price_product_code(
                            self.product_code, self.product_barcode, product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id, product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id, product.product_maker_code,
                            self.order_id.partner_id.customer_code, self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date)
                        self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date)
                    else:
                        self.price_include_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode, product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id, product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id, product.product_maker_code,
                            self.order_id.partner_id.customer_code, self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date)
                        self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id,
                            self.order_id.quotations_date) / (product.product_tax_rate / 100 + 1)

                    self.compute_price_unit()
                    self.compute_line_amount()
                    self.compute_line_tax_amount()
                    return
            # else
            self.product_barcode = ''
        else:
            self.changed_fields.remove('product_code')

    @api.onchange('product_barcode')
    def _onchange_product_barcode(self):
        if 'product_barcode' not in self.changed_fields:

            if self.product_barcode:
                product = self.env['product.product'].search([
                    ['barcode', '=', self.product_barcode]
                ])
                if product:
                    self.changed_fields.append('product_code')
                    self.product_id = product.id
                    if product.product_code_1:
                        self.product_code = product.product_code_1
                    elif product.product_code_2:
                        self.product_code = product.product_code_2
                    elif product.product_code_3:
                        self.product_code = product.product_code_3
                    elif product.product_code_4:
                        self.product_code = product.product_code_4
                    elif product.product_code_5:
                        self.product_code = product.product_code_5
                    elif product.product_code_6:
                        self.product_code = product.product_code_6
                    setting_price = '1'
                    if product.setting_price:
                        setting_price = product.setting_price[5:]
                    if product.product_tax_category == 'exempt':
                        self.price_include_tax = self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date)
                    elif product.product_tax_category == 'foreign':
                        self.price_include_tax = (product.product_tax_rate / 100 + 1) * self.set_price_product_code(
                            self.product_code, self.product_barcode, product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id, product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id, product.product_maker_code,
                            self.order_id.partner_id.customer_code, self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date)
                        self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date)
                    else:
                        self.price_include_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode, product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id, product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id, product.product_maker_code,
                            self.order_id.partner_id.customer_code, self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date)
                        self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.quotations_date) / (
                                                        product.product_tax_rate / 100 + 1)
                    self.compute_price_unit()
                    self.compute_line_amount()
                    self.compute_line_tax_amount()
                    return

            # Else
            self.product_code = ''
        else:
            self.changed_fields.remove('product_barcode')

    @api.onchange('refer_detail_history')
    def _get_detail_history(self):
        if self.refer_detail_history:
            data = self.refer_detail_history

            if not data.display_type:
                self.changed_fields = ['product_code', 'product_barcode', 'product_id']
                self.class_item = data.class_item
                self.product_id = data.product_id
                self.product_name = data.product_name
                self.product_name2 = data.product_name2
                self.product_code = data.product_code
                self.product_barcode = data.product_barcode
                self.product_maker_name = data.product_maker_name
                self.product_standard_number = data.product_standard_number
                self.product_standard_price = data.product_standard_price
                self.product_uom_qty = data.product_uom_qty
                self.product_uom_id = data.product_uom_id
                self.price_unit = data.price_unit
                self.cost = data.cost
                self.line_amount = data.line_amount
                self.tax_rate = data.tax_rate
                self.line_tax_amount = data.line_tax_amount
                self.description = data.description

            self.name = data.name
            self.display_type = data.display_type

    @api.onchange('product_id')
    def _get_detail_product(self):
        if 'product_id' not in self.changed_fields:
            for line in self:
                if not line.product_id or line.display_type in ('line_section', 'line_note'):
                    line.product_id = ''
                    line.product_name = ''
                    line.product_name2 = ''
                    line.product_uom_id = ''
                    line.product_maker_name = ''
                    line.product_standard_number = ''
                    line.product_standard_price = 0
                    line.cost = 0
                    line.tax_rate = 0
                    continue

                line.product_id = line.product_id or ''
                line.product_name = line.product_id.name or ''
                line.product_name2 = line.product_id.product_custom_goodsnamef or ''
                line.product_uom_id = line.product_id.product_uom_custom or ''
                line.product_maker_name = line.product_id.product_maker_name or ''
                line.product_standard_number = line.product_id.product_custom_standardnumber or ''
                line.product_standard_price = line.product_id.standard_price or 0.00
                line.cost = line.product_id.cost or 0.00
                line.tax_rate = line.product_id.product_tax_rate or 0.00

    @api.onchange('class_item')
    def _onchange_class_item(self):
        for line in self:
            if line.class_item == 'サンプル':
                # Check product sample
                sample_product_ids = self.env['product.product'].search([('barcode', '=', '0000000000000')])
                if sample_product_ids:
                    line.product_id = sample_product_ids
                else:
                    raise ValidationError(_('Must create a sample product in the product master\n- JANコード: 0000000000000'))

    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes
            # line.tax_rate = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())

    # @api.depends('tax_id', 'order_id.tax_method', 'order_id.customer_tax_rounding', 'class_item', 'tax_rate')
    # def compute_tax_rate(self):
    #     for line in self:
    #         line.tax_rate = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())

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

            if line.class_item == '通常':
                if line.product_uom_qty < 0:
                    line.product_uom_qty = line.product_uom_qty * (-1)
            elif line.class_item in ('返品', '値引'):
                if line.product_uom_qty > 0:
                    line.product_uom_qty = line.product_uom_qty * (-1)
            elif line.class_item == 'サンプル':
                line.product_uom_qty = 0
                line.price_unit = 0
                line.tax_rate = 0
                line.product_maker_name = ''
                line.product_standard_number = ''
                line.description = ''
                line.product_uom_id = ''

            line.compute_price_unit()
            line.compute_line_amount()
            line.compute_line_tax_amount()

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        for line in self:
            exchange_rate = 1
            #TH - code
            if line.product_id.product_tax_category == 'foreign':
                if line.order_id.partner_id.customer_apply_rate == "customer":
                    if line.order_id.partner_id.customer_rate and line.order_id.partner_id.customer_rate > 0:
                        exchange_rate = line.order_id.partner_id.customer_rate / 100
                elif line.order_id.partner_id.customer_apply_rate == "category":
                    if line.product_id.product_class_code_lv4 \
                            and line.product_id.product_class_code_lv4.product_class_rate \
                            and line.product_id.product_class_code_lv4.product_class_rate > 0:
                        exchange_rate = line.product_id.product_class_code_lv4.product_class_rate / 100

                if line.product_id.product_tax_category == 'exempt':
                    line.price_no_tax = line.price_include_tax = line.price_unit / exchange_rate
                else:
                    if line.order_id.tax_method == 'internal_tax':
                        line.price_include_tax = line.price_unit / exchange_rate
                        line.price_no_tax = line.price_unit / (line.tax_rate / 100 + 1) / exchange_rate
                    elif line.order_id.tax_method == 'custom_tax':
                        if line.product_id.product_tax_category == 'foreign':
                            line.price_no_tax = line.price_unit / exchange_rate
                            line.price_include_tax = line.price_unit * (line.tax_rate / 100 + 1) / exchange_rate
                        elif line.product_id.product_tax_category == 'internal':
                            line.price_include_tax = line.price_unit / exchange_rate
                            line.price_no_tax = line.price_unit / (line.tax_rate / 100 + 1) / exchange_rate
                        else:
                            line.price_no_tax = line.price_include_tax = line.price_unit / exchange_rate
                    else:
                        line.price_no_tax = line.price_unit / exchange_rate
                        line.price_include_tax = line.price_unit * (line.tax_rate / 100 + 1) / exchange_rate
            elif line.product_id.product_tax_category == 'internal':
                line.price_include_tax = line.price_unit / exchange_rate
                line.price_no_tax = line.price_unit / (line.tax_rate / 100 + 1) / exchange_rate
            else:
                line.price_no_tax = line.price_include_tax = line.price_unit / exchange_rate
            #TH - done

    @api.depends('order_id.tax_method')
    def compute_price_unit(self):
        for line in self:
            # todo set price follow product code
            #TH - code
            if line.product_id.product_tax_category == 'foreign':
                if line.order_id.tax_method == 'internal_tax':
                    price_unit = line.price_include_tax
                elif line.order_id.tax_method == 'custom_tax':
                    if line.product_id.product_tax_category == 'foreign':
                        price_unit = line.price_no_tax
                    elif line.product_id.product_tax_category == 'internal':
                        price_unit = line.price_include_tax
                    else:
                        price_unit = line.price_no_tax
                else:
                    price_unit = line.price_no_tax

                if line.order_id.partner_id.customer_apply_rate == "customer":
                    if line.order_id.partner_id.customer_rate and line.order_id.partner_id.customer_rate > 0:
                        price_unit = price_unit * line.order_id.partner_id.customer_rate / 100
                elif line.order_id.partner_id.customer_apply_rate == "category":
                    if line.product_id.product_class_code_lv4 \
                            and line.product_id.product_class_code_lv4.product_class_rate \
                            and line.product_id.product_class_code_lv4.product_class_rate > 0:
                        price_unit = price_unit * line.product_id.product_class_code_lv4.product_class_rate / 100
            elif line.product_id.product_tax_category == 'internal':
                price_unit = line.price_include_tax
            else:
                price_unit = line.price_no_tax
            #TH - done
            if line.copy_history_flag:
                price_unit = line.price_unit
            if line.class_item == 'サンプル':
                line.price_unit = 0
            else:
                line.price_unit = price_unit

    def compute_line_amount(self):
        for line in self:
            line.line_amount = self.get_compute_line_amount(line.price_unit, line.discount, line.product_uom_qty,
                                                            line.order_id.customer_tax_rounding)

    def get_compute_line_amount(self, price_unit=0, discount=0, quantity=0, line_rounding='round'):
        result = price_unit * quantity - (discount * price_unit / 100) * quantity
        return rounding(result, 0, line_rounding)

    def compute_line_tax_amount(self):
        for line in self:
            #TH - code
            if line.product_id.product_tax_category == 'foreign':
                if (line.order_id.tax_method == 'foreign_tax'
                    and line.product_id.product_tax_category != 'exempt') \
                        or (line.order_id.tax_method == 'custom_tax'
                            and line.product_id.product_tax_category == 'foreign'):
                    # total_line_tax = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())
                    line.line_tax_amount = self.get_compute_line_tax_amount(line.line_amount,
                                                                            line.tax_rate,
                                                                            line.order_id.customer_tax_rounding,
                                                                            line.class_item)
                else:
                    line.line_tax_amount = 0
            else:
                line.line_tax_amount = 0
            #TH - done
            line._onchange_price_unit()

    # Set tax for tax_method = voucher
    voucher_line_tax_amount = fields.Float('Voucher Line Tax Amount', compute='set_voucher_line_tax_amount', default=0)

    def set_voucher_line_tax_amount(self):
        for re in self:
            if (re.order_id.tax_method == 'voucher'
                    and re.product_id.product_tax_category != 'exempt'):
                re.voucher_line_tax_amount = (re.line_amount * re.tax_rate) / 100
            else:
                re.voucher_line_tax_amount = 0

    def get_compute_line_tax_amount(self, line_amount, line_taxes, line_rounding, line_type):
        if line_amount != 0:
            return rounding(line_amount * line_taxes / 100, 0, line_rounding)
        else:
            return 0

    # def button_update(self):
    #     products = self.env["sale.order.line"].search([('id', 'in', self.ids)])
    #     self.order_id.order_line = [(0, False, {
    #         'class_item': products.class_item,
    #         'customer_lead': products.customer_lead,
    #         'description': products.description,
    #         'discount': products.discount,
    #         'display_type': products.display_type,
    #         'invoice_status': products.invoice_status,
    #         'name': products.name,
    #         'order_id': products.order_id,
    #         'price_include_tax': products.price_include_tax,
    #         'price_no_tax': products.price_no_tax,
    #         'price_unit': products.price_unit,
    #         'product_barcode': products.product_barcode,
    #         'product_code': products.product_code,
    #         'product_id': products.product_id.id,
    #         'product_maker_name': products.product_maker_name,
    #         'product_name': products.product_name,
    #         'product_name2': products.product_name2,
    #         'product_standard_number': products.product_standard_number,
    #         'product_uom': products.product_uom.id,
    #         'product_uom_id': products.product_uom_id,
    #         'product_uom_qty': products.product_uom_qty,
    #         'qty_delivered': products.qty_delivered,
    #         'qty_delivered_manual': products.qty_delivered_manual,
    #         'quotation_custom_line_no': len(self.order_id.order_line) + 1,
    #         'sequence': products.sequence,
    #         'state': products.state,
    #         'tax_rate': products.tax_rate,
    #         'copy_history_flag': True,
    #     })]

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        odoo/models.py
        """
        ctx = self._context.copy()
        if ctx.get('have_advance_search'):
            domain = []
            check = 0
            arr = ["partner_id", "partner_id.name", "order_id.sales_rep", "product_code", "product_barcode",
                   "product_standard_number", "product_maker_name", "product_name"]
            for se in args:
                if se[0] == '&':
                    continue
                if se[0] == 'search_category' and se[2] == 'equal':
                    check = 1
                if check == 1 and se[0] in arr:
                    se[1] = '=ilike'
                if se[0] != 'search_category':
                    domain += [se]
                # TH - custom domain
                if se[0] == 'document_no':
                    string_middle = ''
                    if len(se[2]) < 7:
                        for i in range(6 - len(se[2])):
                            string_middle += '0'
                        string_middle = '1' + string_middle
                    if len(se[2]) < 11:
                        se[2] = ''.join(["ARQ-", string_middle, se[2]])
                # TH - done
            args = domain
        res = super(QuotationsLinesCustom, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res


class QuotationReportHeaderCustom(models.Model):
    _name = "sale.order.reportheader"
    _rec_name = 'name'

    name = fields.Char(string='Report Header')
