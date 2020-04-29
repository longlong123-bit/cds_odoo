# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassEmployeeCusstom(models.Model):
    _inherit = ["hr.employee"]

    employee_code = fields.Char('Employee Code')



