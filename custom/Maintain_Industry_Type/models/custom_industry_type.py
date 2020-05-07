# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClassIndustry(models.Model):
    _inherit = 'res.partner.industry'

    industry_code = fields.Char('Industry Code')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(industry_code)', 'The code of the industry must be unique!')
    ]

    @api.constrains('industry_code')
    def _check_unique_searchkey(self):
        exists = self.env['res.partner.industry'].search(
            [('industry_code', '=', self.industry_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code of the industry must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'industry_code': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(ClassIndustry, self).copy(default)