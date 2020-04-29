# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassCreateCompany(models.Model):
    _name = 'res.company'
    _inherit = ['res.company']

    company_payment_term = fields.Many2one('account.payment.term', string='Payment Term')

