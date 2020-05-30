# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassCountryState(models.Model):
    _inherit = 'res.country.state'

    name = fields.Char(string='State Name')
    code = fields.Char(string='State Code', required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True,
                                 default=lambda self: self.env['res.country'].search([('code', '=', 'JP')]))
    active = fields.Boolean('Active', default=True)

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            code_show =  str(record.code) + " - " + name
            result.append((record.id, code_show))
        return result


