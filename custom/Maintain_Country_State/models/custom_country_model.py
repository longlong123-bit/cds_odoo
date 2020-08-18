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
        super(ClassCountryState, self).name_get()
        result = []
        for record in self:
            name = record.name
            if 'show_code' in self.env.context:
                code_show = str(record.code)
            else:
                code_show = str(record.code) + " - " + name
            result.append((record.id, code_show))
        return result


