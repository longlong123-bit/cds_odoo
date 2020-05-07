# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassCreateCompany(models.Model):
    _name = 'res.company'
    _inherit = ['res.company']

    name = fields.Char('Company Name')
    company_payment_term = fields.Many2one('account.payment.term', string='Payment Term')
    company_fax = fields.Char('Fax')
    company_closing_date = fields.Date('Closing Date')
    company_bank_name_1 = fields.Char('Bank Name 1')
    company_bank_name_2 = fields.Char('Bank Name 2')
    company_bank_name_3 = fields.Char('Bank Name 3')
    company_bank_name_4 = fields.Char('Bank Name 4')
    company_bank_account_1 = fields.Integer('Bank Account 1')
    company_bank_account_2 = fields.Integer('Bank Account 2')
    company_bank_account_3 = fields.Integer('Bank Account 3')
    company_bank_account_4 = fields.Integer('Bank Account 4')
    active = fields.Boolean('Active', default=True)

