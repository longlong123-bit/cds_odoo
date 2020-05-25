# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClassTaxRate(models.Model):
    _inherit = 'account.tax'

    tax_rate_code = fields.Char(string='Tax Rate Code')
    name = fields.Char('Tax Rate Name')
    active = fields.Boolean('Active', default=True)
    amount = fields.Float(required=True, digits=(16, 4), string='Rate')

    _sql_constraints = [
        ('name_code_uniq', 'unique(employee_code)', 'The code must be unique!')
    ]

    @api.constrains('tax_rate_code')
    def _check_unique_searchkey(self):
        exists = self.env['account.tax'].search(
            [('tax_rate_code', '=', self.tax_rate_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'tax_rate_code': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(ClassTaxRate, self).copy(default)



