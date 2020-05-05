# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassBillSchema(models.Model):
    _name = 'tax.rate'

    tax_rate_code = fields.Char('Tax Rate Code')
    tax_rate_name = fields.Char('Tax Rate Name')



