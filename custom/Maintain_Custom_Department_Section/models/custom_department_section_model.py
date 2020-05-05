# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassDepartmentCustom(models.Model):
    _name = 'section.model'

    section_name = fields.Char('Section Name')
    department_section_code = fields.Char('Section Code')
    parent_department_code = fields.Char('Parent Department Code')
    department_code1 = fields.Many2one('hr.department')



