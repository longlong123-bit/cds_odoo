# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassBillSchema(models.Model):
    _inherit = 'account.tax'

    tax_rate_code = fields.Char(string='Tax Rate Code')
    tax_rate_name = fields.Char('Tax Rate Name')
    active = fields.Boolean('Active', default=True)



