# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ClassPartnerGroup(models.Model):
    _name = 'business.partner.group.custom'

    partner_group_code = fields.Char('Partner Group Code', required=True)
    name = fields.Char('name', required=True)
    description =fields.Char('description')
    active = fields.Boolean('isactive', default=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(partner_group_code)', 'The code must be unique!')
    ]

    @api.constrains('partner_group_code')
    def _check_unique_searchkey(self):
        exists = self.env['business.partner.group.custom'].search(
            [('partner_group_code', '=', self.partner_group_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'partner_group_code': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(ClassPartnerGroup, self).copy(default)


