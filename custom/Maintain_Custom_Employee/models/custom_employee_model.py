# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassEmployeeCusstom(models.Model):
    _inherit = ["hr.employee"]

    employee_code = fields.Char('Employee Code')
    employee_password = fields.Char('Password')
    employee_section_id = fields.Many2one('section.model', string='Section Code')



