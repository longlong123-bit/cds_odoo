# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ClassDepartmentSectionCustom(models.Model):
    _name = 'section.model'

    name = fields.Char('Section Name')
    department_section_code = fields.Char('Section Code')
    parent_department_code = fields.Char('Parent Department Code')
    department_code1 = fields.Many2one('hr.department')
    department_fake_id = fields.Char('id')

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

    # def write(self, vals):
    #
    #     department = self.env['hr.department'].create({
    #         'name': vals['name'],
    #         'parent_id': vals['department_code1'],
    #         'department_code': vals['department_section_code']
    #     })
    #     vals['department_fake_id'] = department.id
    #
    #     section = super(ClassDepartmentSectionCustom, self).write(vals)
    #     return section
