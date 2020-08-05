# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClassClosingDate(models.Model):
    _name = 'closing.date'

    closing_date_code = fields.Char('Closing Date Code')
    name = fields.Char('Closing Date Name')
    start_day = fields.Integer('Start Date', size=2)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(closing_date_code)', 'The code must be unique!')
    ]

    @api.constrains('start_day')
    def _check_maximum_day(self):
        if self.start_day > 99 or self.start_day < 1:
            raise ValidationError(_('The day must be 1 to 99!'))

    @api.constrains('closing_date_code')
    def _check_unique_searchkey(self):
        exists = self.env['closing.date'].search(
            [('closing_date_code', '=', self.closing_date_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'closing_date_code': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(ClassClosingDate, self).copy(default)

    # def create(self, vals):
    #     if vals['closing_date_code'] == False:
    #         raise ValidationError(_('The code must be create!'))



