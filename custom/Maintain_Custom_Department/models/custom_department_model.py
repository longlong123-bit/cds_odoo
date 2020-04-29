# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassDepartmentCustom(models.Model):
    _inherit = ['hr.department']

    department_code = fields.Char('Department Code')



