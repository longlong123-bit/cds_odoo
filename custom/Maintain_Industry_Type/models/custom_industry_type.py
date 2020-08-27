# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

check_industry_code = False

class ClassIndustry(models.Model):
    _inherit = 'res.partner.industry'

    name = fields.Char(string='Industry Name', translate=True)
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

    def name_get(self):
        result = []
        global check_industry_code
        for record in self:
            name = record.name
            if 'showcode' in self.env.context or 'master_price_list' in self.env.context:
                code_show = str(record.industry_code)
            else:
                if check_industry_code:
                    check_industry_code = False
                    code_show = str(record.industry_code)
                else:
                    check_industry_code = False
                    code_show = str(record.industry_code) + " - " + name
            result.append((record.id, code_show))
        return result
