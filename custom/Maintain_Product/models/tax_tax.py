
from odoo import api, fields, models


class TaxTax(models.Model):
    _name = 'tax.tax'
    _description = 'Taxes'

    code = fields.Char(string='Tax Rate Code', required=True)
    name = fields.Char(string='Tax Rate Name', required=True)
    amount = fields.Float(string='Rate')
    active = fields.Boolean(string='Active', default=True)
