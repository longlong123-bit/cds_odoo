# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassDepartmentCustom(models.Model):
    _inherit = ['hr.department']

    department_code = fields.Char('Department Code')
    parent_department_code = fields.Many2one( 'company.office.custom','Parent Department Code')
    section_id = fields.One2many('section.model', 'department_code1', 'Section', copy=True)