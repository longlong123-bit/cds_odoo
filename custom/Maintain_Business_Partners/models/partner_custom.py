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


    def _get_default_partner_group(self):
        return self.env["business.partner.group.custom"].search([], limit=1, order='id').id

    @api.model
    def _default_payment_terms(self):
        return self.env['account.payment.term'].search([], limit=1)

    @api.model
    def _default_price_list(self):
        return self.env['product.pricelist'].search([], limit=1, order='id').id

    # display_name = fields.Char(string="Name")
    customer_namef = fields.Char('namef')
    customer_display_name = fields.Char(string='Name 3')
    customer_extra_name = fields.Char('nameextra')
    search_key_partner = fields.Char('search_key', default=lambda self:_(''))
    _rec_name = 'search_key_partner'
    address3 = fields.Char('address3')
    partner_group = fields.Many2one('business.partner.group.custom', default=_get_default_partner_group)
    fax = fields.Char('fax')
    # todo Sale & purchase
    # todo Purchase group
    payment_rule = fields.Selection(
        [('rule_cash', 'Cash'),('rule_check', 'Check'),('rule_credit','Credit Card'),('rule_direct_debit','Direct Debit'),
         ('rule_deposit','Direct Deposit'),('rule_on_credit','On Credit')], 'payment_rule', store=True,
         )

    payment_terms = fields.Many2one('account.payment.term', 'payment_terms',company_dependent=True,
        default=lambda self: self.env['account.payment.term'].search([('id','=', 1)]))
    # todo bill schema
    bill_schema = fields.Many2one('bill.schema.custom', store=True)
    # bill_schema = fields.Selection([('blank', ''),('bill_1', 'まとめ請求書作成条件Test01')], default='blank', store=True,)
    is_so_tax_exempt = fields.Boolean('so tax exempt')
    # todo Sale group
    discount_schema = fields.Many2one('discount.schema', string='Discount Schema')
    user_id = fields.Many2one('res.users', string='Representative/Agent', domain="[('share', '=', False)]", default=lambda self: self.env.user)
    sale_person = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    flat_discount = fields.Float('Float Discount')
    so_tax_rounding = fields.Many2one('account.cash.rounding', string='so tax rounding')
    credit_status = fields.Selection(
        [('credit_hold', 'Credit Hold'),('credit_ok','Credit Ok'),('credit_stop','Credit Stop'),('credit_watch','Credit Watch'),('credit_no_check','No Credit Check')])
    # todo price list
    property_product_pricelist = fields.Many2one(
        'product.pricelist', 'Pricelist', compute='_compute_product_pricelist',
        inverse="_inverse_product_pricelist", company_dependent=False,default=_default_price_list,
        help="This pricelist will be used, instead of the default one, for sales to the current partner")
    pricelist_custom = fields.Char('price_list_custom', default='販売(税抜:JPY)')
    credit_limit = fields.Integer('Credit Limit')
    billformrequireflag = fields.Char('billformrequireflag', default="要")
    first_sale = fields.Date('first_sale')
    # internal_user_partner_custom = fields.Many2one('res.users', domain=[('share', '=', False)])
    exchangeenddate = fields.Date('exchangeenddate')
    zip_code = fields.Char('zip_code',change_default=True)
    salesslipformcd = fields.Selection([('form_1', '指定なし'),('form_2', '通常'),('form_3', '専伝・仮伝')],'salesslipformcd', default='form_2')
    description = fields.Text('Description')
    invoice_print_format = fields.Many2one('invoice.print.custom')
    document_copies = fields.Integer('Document Copies')
    discount_printed = fields.Boolean('Discount Printed')
    write_date = fields.Datetime('Update')
    active = fields.Boolean('Active')
    open_balance = fields.Integer('Open Balance')
    actual_life_time_value = fields.Monetary(string='Actual Life Time Value')
    customer_tax = fields.Char('Tax')
    customer_classification_rate = fields.Char('classification rate')
    customer_class_rate = fields.Float('class rate')
    customer_isdateprinted = fields.Boolean('isdateprinted')
    action_view_invoice = fields.Char('avi')


    def name_get(self):
        result = []
        for record in self:
            name = record.name
            search_key_show =  str(record.search_key_partner) + " - " + name
            result.append((record.id, search_key_show))
        return result


    @api.constrains('search_key_partner')
    def _check_unique_searchkey(self):
        search_partner_mode = self.env.context.get('res_partner_search_mode')
        is_customer = search_partner_mode == 'customer'
        if is_customer:
            exists = self.env['res.partner'].search(
                [('search_key_partner', '=', self.search_key_partner), ('id', '!=', self.id)])
            if exists:
                raise ValidationError(_('The Search Key has already been registered'))

    @api.model
    def create(self, vals):
        print('create')
        search_partner_mode = self.env.context.get('res_partner_search_mode')
        is_customer = search_partner_mode == 'customer'
        print("childrennnnnnnnnnnnnnnnnnnnnnnn")
        print(search_partner_mode)
        if is_customer:
            print("childrennnnnnnnnnnnnnnnnnnnnnnn")
            # check search key
            if not vals['search_key_partner']:
                vals['search_key_partner'] = self.env['ir.sequence'].next_by_code('customer.search.key.sequence') or _(' ')
            # search_key_count = self.env['res.partner'].search_count(
            #     [('search_key_partner', '=', vals['search_key_partner'])])
            # if search_key_count > 0:
            #     raise ValidationError(_('The Search Key has already been registered'))

        return super(NewClassPartnerCustom, self).create(vals)
    _sql_constraints = [
        ('search_key_partner_uniq', 'unique (search_key_partner)', 'You can not have two users with the same search key !')
    ]


    def copy(self, default=None):
        default = dict(default or {})
        default.update({'search_key_partner': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(NewClassPartnerCustom, self).copy(default)


    @api.model
    def _get_default_address_format(self):
        return "%(street)s\n%(street2)s\n%(address3)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)
