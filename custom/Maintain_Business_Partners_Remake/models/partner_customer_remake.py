# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.test_convert.tests.test_env import record
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from lxml import etree
import simplejson
import re

from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

ADDRESS_FIELDS = ('street', 'street2', 'address3', 'zip', 'city', 'state_id', 'country_id')


class NewClassPartnerCustom(models.Model):
    # _name = 'partner.customer.custom'
    _inherit = 'res.partner'

    @api.model
    def _default_closing_date(self):
        return self.env['closing.date'].search([], limit=1)

    @api.model
    def _default_partner_group(self):
        return self.env['business.partner.group.custom'].search([], limit=1)

    # relation customer
    relation_id = fields.One2many('relation.partner.model', 'partner_id', string='Relation')
    # name
    name = fields.Char(string='Name', size=50)
    # name 2
    customer_name_2 = fields.Char(string='Name 2')
    customer_code = fields.Char(string='Customer Code')
    # 請求先コード
    customer_code_bill = fields.Char(string='Billing Code', store=True)
    customer_get_billing_code = fields.Many2one('res.partner', 'Customer', store=False)
    customer_get_billing_code_name = fields.Char('Name', related='customer_get_billing_code.name')
    customer_name_short = fields.Char(string='Customer Name Short')
    customer_name_kana = fields.Char(string='Customer Name Kana')
    zip_code = fields.Char('Zip')
    street = fields.Char('Address 1', size=40)
    street2 = fields.Char('Address 2')
    # Add to do
    payment_terms = fields.Many2one('account.payment.term', 'Payment Terms', company_dependent=True, required=True,
                                    default=lambda self: self.env['account.payment.term'].search([('id', '=', 1)]))
    address3 = fields.Char('Address 3')
    search_key_partner = fields.Char('Search Key', default=lambda self: _(''))

    customer_fax = fields.Char('Fax')
    customer_phone = fields.Char('Phone')
    customer_state = fields.Many2one('res.country.state', string='State', domain=[('country_id', '=', 113)])
    customer_supplier_group_code = fields.Many2one('business.partner.group.custom', 'Supplier Group Code',
                                                   default=_default_partner_group)
    customer_industry_code = fields.Many2one('res.partner.industry', string='Industry Code')
    # 担当者
    customer_agent = fields.Many2one('hr.employee', string='Representative/Agent')
    # 取引区分コード
    customer_trans_classification_code = fields.Selection([('sale', 'Sale'), ('cash', 'Cash'), ('account', 'Account')],
                                                          string='Transaction classification', default='sale')

    # Chien-NV DEL - change request ９．得意先マスタ_修正200605
    # 消費税区分
    # customer_tax_category = fields.Selection(
    #     [('foreign', 'Foreign Tax'), ('internal', 'Internal Tax'), ('exempt', 'Tax Exempt')],
    #     string='Consumption Tax Category', default='foreign')
    # Chien-NV DEL end

    # 消費税計算区分
    customer_tax_unit = fields.Selection(
        [('detail', 'Detail Unit'), ('voucher', 'Voucher Unit'), ('invoice', 'Invoice Unit')],
        string='Consumption Tax Calculation Category', default='detail')
    # 消費税端数処理
    customer_tax_rounding = fields.Selection(
        [('round', 'Rounding'), ('roundup', 'Round Up'), ('rounddown', 'Round Down')], 'Tax Rounding', default='round')
    # 締日
    customer_closing_date = fields.Many2one('closing.date', 'Closing Date', default=_default_closing_date)
    # 入金方法
    customer_payment_method = fields.Selection([('normal', 'Normal'), ('deposit', 'Deposit')], 'Payment Method',
                                               default='normal')
    # 回収方法
    customer_collect_method = fields.Char('Collect Method')
    payment_rule = fields.Selection(
        [('rule_cash', 'Cash'), ('rule_check', 'Check'), ('rule_credit', 'Credit Card'),
         ('rule_direct_debit', 'Direct Debit'),
         ('rule_deposit', 'Direct Deposit'), ('rule_on_credit', 'On Credit')], 'Collect Method', store=True,
        default='rule_cash'
    )
    # 回収月、回収日
    customer_collect_circle = fields.Char('Collect Circle')
    # 掛率設定
    customer_apply_rate = fields.Selection([('category', 'Category'), ('customer', 'Customer')], 'Apply Rate')
    # 掛率
    customer_rate = fields.Float('Hang Rate')
    # 請求値引区分
    customer_bill_discount = fields.Boolean('Bill Discount', default=False)
    # 請求値引率
    customer_bill_discount_rate = fields.Float('Bill Discount Rate')
    # 抜粋請求区分
    customer_except_request = fields.Boolean('Excerpt Request')
    # 売上伝票印刷
    customer_print_voucher = fields.Boolean('Print Voucher', default=True)
    # 売上伝票選択
    customer_select_sales_slip = fields.Selection([('slip1', '売上伝票(書式1)')], 'Sales Slip', default="slip1")
    # 納品書選択
    customer_delivery_note = fields.Selection([('note1', '通常'), ('note2', 'ヤマサタイプ'),('note3','岡田土建タイプ'),('note4','銚子信用金庫')], 'Delivery Note',
                                              default="note1")
    # 売上伝票日付印字
    customer_print_sales_slip_date = fields.Boolean('Print Sales Slip Date', default=True)
    # 請求書印刷
    customer_print_invoice = fields.Boolean('Print Invoice', default=True)
    # 請求書選択
    customer_select_invoice = fields.Selection([('form1', '請求書(書式1)'), ('note2', '請求書(書式2)')], 'Select Invoice',
                                               default="form1")
    # 請求書日付印刷
    customer_print_invoice_date = fields.Boolean('Print Invoice Date', default=True)
    # その他CD
    customer_other_cd = fields.Char('Customer CD')
    # 備考
    customer_comment = fields.Char('Comment')
    # 取引区分コード
    # customer_office = fields.Char('Customer Office')

    _sql_constraints = [
        ('name_code_uniq', 'unique(customer_code)', 'The code must be unique!')
    ]

    def name_get(self):
        result = []
        for record in self:
            search_key_show = str(record.customer_code)
            result.append((record.id, search_key_show))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if not recs:
            recs = self.search([('customer_code', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.constrains('customer_code')
    def _check_unique_searchkey(self):
        exists = self.env['res.partner'].search(
            [('customer_code', '=', self.customer_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'customer_code': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(NewClassPartnerCustom, self).copy(default)

    @api.onchange('name')
    def _get_name_short(self):
        for rec in self:
            if rec.name and not rec.customer_name_short:
                rec.customer_name_short = rec.name

    # get customer billing
    @api.onchange('customer_code')
    def _get_billing_code_by_code(self):
        if self.customer_code:
            self.customer_code_bill = self.customer_code
            code_count = self.env['res.partner'].search_count([('customer_code', '=', self.customer_code)])
            if code_count > 0:
                raise ValidationError(_('The code must be unique!'))
        return {}


    @api.constrains('customer_bill_discount', 'customer_bill_discount_rate', 'customer_rate')
    def _check_min_max(self):
        if not 0 <= self.customer_bill_discount_rate <= 100:
            if self.customer_bill_discount is True:
                raise ValidationError(_('Customer bill discount rate must be greater than 0 and less than 100 !'))
        if not 0 <= self.customer_rate <= 100:
            raise ValidationError(_('Customer rate must be greater than 0 and less than 100 !'))

    # todo filter res partner
    def _get_customer_depend_billing_code(self):
        self._cr.execute('''
                    SELECT *
                    FROM res_partner partner
                    WHERE partner.customer_code = partner.customer_code_bill
                ''', [tuple(self.ids)])
        query_res = self._cr.fetchall()
        return query_res

    #  get billing code from combobox
    @api.onchange('customer_get_billing_code')
    def _get_billing_code_by_customer(self):
        for rec in self:
            if rec.customer_get_billing_code:
                rec.customer_code_bill = rec.customer_get_billing_code.customer_code_bill

    @api.model
    def create(self, vals):
        if not vals['customer_code_bill']:
            vals['customer_code_bill'] = vals['customer_code']
        return super(NewClassPartnerCustom, self).create(vals)

class ClassRelationPartnerCustom(models.Model):
    _name = 'relation.partner.model'

    partner_id = fields.Many2one('res.partner', ondelete='cascade',
                                 required=True, index=True)
    relate_customer_organization = fields.Many2one('res.company', string='Organization')
    name = fields.Char('Name')
    relate_business_partner = fields.Many2one('res.partner', string='Customer')
    relate_partner_location = fields.Char('Partner Location')
    relate_related_partner = fields.Many2one('company.office.custom', string='Related Partner')
    relate_related_partner_location = fields.Char('Related Partner Location')
    relate_ship_address = fields.Boolean('Ship Address')
    relate_invoic_address = fields.Boolean('Invoice Address')
    relate_payfrom_address = fields.Boolean('Pay-From Address')
    relate_remitto_address = fields.Boolean('Remit-To Address')
    active = fields.Boolean('Active', default=True)

    def button_details(self):
        view = {
            'name': _('Detail'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'relation.partner.model',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': True,
            'res_id': self.id,
        }
        return view

    def action_close_dialog(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('relate_business_partner')
    def _get_location_business_partner(self):
        for rec in self:
            if rec.relate_business_partner:
                rec.relate_partner_location = rec.relate_business_partner.street

    @api.onchange('relate_related_partner')
    def _get_location_related_business_partner(self):
        for rec in self:
            if rec.relate_related_partner:
                rec.relate_related_partner_location = rec.relate_related_partner.street
