# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClassEmployeeCustom(models.Model):
    _inherit = ["hr.employee"]
    _order = 'employee_code asc, name asc'

    name = fields.Char('Employee Name')
    employee_code = fields.Char('Employee Code')
    employee_password = fields.Char('Password')
    employee_section_id = fields.Many2one('section.model', string='Section Code')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(employee_code)', 'The code must be unique!')
    ]

    @api.constrains('employee_code')
    def _check_unique_searchkey(self):
        exists = self.env['hr.employee'].search(
            [('employee_code', '=', self.employee_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'employee_code': ''})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(ClassEmployeeCustom, self).copy(default)

    @api.model
    def create(self, vals):
        if vals['employee_section_id']:
            section = self.env['section.model'].search([('id', '=', vals['employee_section_id'])])
            vals['department_id'] = int(section.department_fake_id)

        employee = super(ClassEmployeeCustom, self).create(vals)

        return employee

    def write(self, vals):
        if 'employee_section_id' in vals:
            section = self.env['section.model'].search([('id', '=', vals['employee_section_id'])])
            vals['department_id'] = int(section.department_fake_id)

        employee = super(ClassEmployeeCustom, self).write(vals)

        return employee




