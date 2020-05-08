# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClassDepartmentCustom(models.Model):
    _inherit = ['hr.department']

    name = fields.Char(string='Department Name')
    department_code = fields.Char('Department Code')
    parent_department_code = fields.Many2one( 'company.office.custom','Parent Department Code')
    section_id = fields.One2many('section.model', 'department_code1', 'Section', copy=True)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(department_code)', 'The code of the Department must be unique!')
    ]

    @api.constrains('department_code')
    def _check_unique_searchkey(self):
        exists = self.env['hr.department'].search(
            [('department_code', '=', self.department_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code of the Department must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'department_code': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(ClassDepartmentCustom, self).copy(default)

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            search_key_show =  str(record.department_code) + " - " + name
            result.append((record.id, search_key_show))
        return result