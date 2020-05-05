# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassEmployeeCusstom(models.Model):
    _inherit = ["hr.employee"]

    employee_code = fields.Char('Employee Code')
    employee_password = fields.Char('Password')
    employee_section_id = fields.Many2one('section.model', string='Section Code')

    @api.model
    def create(self, vals):
        if vals['employee_section_id']:
            section = self.env['section.model'].search([('id', '=', vals['employee_section_id'])])
            vals['department_id'] = int(section.department_fake_id)

        employee = super(ClassEmployeeCusstom, self).create(vals)

        return employee

    def write(self, vals):
        if vals['employee_section_id']:
            section = self.env['section.model'].search([('id', '=', vals['employee_section_id'])])
            vals['department_id'] = int(section.department_fake_id)

        employee = super(ClassEmployeeCusstom, self).write(vals)

        return employee



