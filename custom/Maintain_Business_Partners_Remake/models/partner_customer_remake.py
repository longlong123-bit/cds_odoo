# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.test_convert.tests.test_env import record
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from lxml import etree
import simplejson

from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

ADDRESS_FIELDS = ('street', 'street2', 'address3', 'zip', 'city', 'state_id', 'country_id')

class NewClassPartnerCustom(models.Model):
    # _name = 'partner.customer.custom'
    _inherit = 'res.partner'

    name = fields.Char(string='Customer Name')
    customer_code = fields.Char(string='Customer Code')
    # 請求先コード
    customer_code_bill = fields.Char(string='Billing Code')
    customer_name_short = fields.Char(string='Customer Name Short')
    customer_name_kana = fields.Char(string='Customer Name Kana')
    zip_code = fields.Char('Zip')
    street = fields.Char('Address 1')
    street2 = fields.Char('Address 2')
    customer_fax = fields.Char('Fax')
    customer_phone = fields.Char('Phone')
    customer_state = fields.Many2one('res.country.state', string='State')
    customer_supplier_group_code = fields.Char('Supplier Group Code')
    customer_industry_code = fields.Many2one('res.partner.industry', string='Industry Code')
    # 担当者
    customer_agent = fields.Many2one('res.users', string='Representative/Agent')
    # 取引区分コード
    customer_trans_classification_code = fields.Selection([('sale','Sale'),('cash','Cash'), ('account','Account')], string='Transaction classification')
    # 消費税区分
    customer_tax_category = fields.Selection([('foreign','Foreign Tax'),('internal','Internal Tax'), ('exempt','Tax Exempt')], string='Consumption Tax Category')
    # 消費税計算区分
    customer_tax_unit = fields.Selection(
        [('detail', 'Detail Unit'), ('voucher', 'Voucher Unit'), ('invoice', 'Invoice Unit')],
        string='Consumption Tax Calculation Category')
    # 消費税端数処理
    customer_tax_rounding = fields.Selection([('round', 'Rounding'), ('roundup', 'Round Up'), ('rounddown', 'Round Down')] ,'Tax Rounding')
     # 締日
    customer_closing_date = fields.Many2one( 'closing.date' ,'Closing Date')
    # 入金方法
    customer_payment_method = fields.Selection([('normal', 'Normal'), ('deposit', 'Deposit')], 'Payment Method')
    # 回収方法
    customer_collect_method = fields.Char('Collect Method')
    # 回収月、回収日
    customer_collect_circle = fields.Char('Collect Circle')
    # 掛率設定
    customer_apply_rate = fields.Selection([('category', 'Category'), ('customer', 'Customer')],'Apply Rate')
    # 掛率
    customer_rate = fields.Char('Hang Rate')
    # 請求値引区分
    customer_bill_discount = fields.Char('Bill Discount')
    # 請求値引率
    customer_bill_discount_rate = fields.Char('Bill Discount Rate')
    # 抜粋請求区分
    customer_except_request = fields.Boolean('Excerpt Request')
    # 売上伝票印刷
    customer_print_voucher = fields.Boolean('Print Voucher')
    # 売上伝票選択
    customer_select_sales_slip = fields.Boolean('Sales Slip')
    # 売上伝票日付印字
    customer_print_sales_slip_date = fields.Boolean('Print Sales Slip Date')
    # 請求書印刷
    customer_print_invoice = fields.Boolean('Print Invoice')
    # 請求書選択
    customer_select_invoice = fields.Boolean('Select Invoice')
    # 請求書日付印刷
    customer_print_invoice_date = fields.Boolean('Print Invoice Date')
    # その他CD
    customer_other_cd = fields.Char('Customer CD')
    # 備考
    customer_comment = fields.Char('Comment')