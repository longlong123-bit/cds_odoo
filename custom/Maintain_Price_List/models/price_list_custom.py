# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PriceListDetail(models.Model):
    _name = 'price.list.custom'
    # _inherit = ['product.pricelist.item']
    _inherit = 'product.template'


    client = fields.Many2one('client.custom', required=True)
    organization = fields.Many2one('res.company', required=True)
    name_price = fields.Char('name', required=True)
    description = fields.Char('description')