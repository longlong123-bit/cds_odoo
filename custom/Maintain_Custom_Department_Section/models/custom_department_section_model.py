# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClassDepartmentSectionCustom(models.Model):
    _name = 'section.model'

    name = fields.Char(string='Section Name')
    department_section_code = fields.Char(string='Section Code')
    parent_department_code = fields.Char(string='Parent Department Code')
    department_code1 = fields.Many2one('hr.department', string='Department Code')
    department_fake_id = fields.Char('id')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(department_section_code)', 'The code must be unique!')
    ]

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            search_key_show =  str(record.department_section_code) + " - " + name
            result.append((record.id, search_key_show))
        return result

    @api.constrains('department_section_code')
    def _check_unique_searchkey(self):
        exists = self.env['section.model'].search(
            [('department_section_code', '=', self.department_section_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'department_section_code': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(ClassDepartmentSectionCustom, self).copy(default)

    @api.model
    def create(self, values):

        department = self.env['hr.department'].create({
            'name': values['name'],
            'parent_id': values['department_code1'],
            'department_code': values['department_section_code']
        })
        values['department_fake_id'] = department.id

        section = super(ClassDepartmentSectionCustom, self).create(values)

        return section

    def write(self, vals):
        name_department = self.name
        if 'name' in vals:
            name_department = vals['name']

        code_department = self.department_code1
        if 'department_code1' in vals:
            code_department = vals['department_code1']
        code_section = self.department_section_code
        if 'department_section_code' in vals:
            code_section = vals['department_section_code']

        department = self.env['hr.department'].search([('id', '=', self.department_fake_id)])
        department.write({
            'name': name_department,
            'parent_id': code_department,
            'department_code': code_section
        })
        section = super(ClassDepartmentSectionCustom, self).write(vals)
        return section

    def unlink(self):
        # OPW-2181568: Delete the chatter message too
        self.env['hr.department'].search([('id', '=', self.department_fake_id)]).unlink()
        return super(ClassDepartmentSectionCustom, self).unlink()

