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
    customer_agent = fields.Many2one('res.users', string='Representative/Agent')
    customer_trans_classification_code = fields.Selection([('sale','Sale'),('cash','Cash'), ('account','Account')], string='Transaction classification')
    customer_tax_category = fields.Selection([('foreign','Foreign Tax'),('internal','Internal Tax'), ('exempt','Tax Exempt')], string='Consumption Tax Category')
    customer_tax_unit = fields.Selection(
        [('detail', 'Detail Unit'), ('voucher', 'Voucher Unit'), ('invoice', 'Invoice Unit')],
        string='')
