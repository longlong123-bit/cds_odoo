# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassBillSchema(models.Model):
    _name = 'closing.date'

    closing_date_code = fields.Char('Closing Date Code')
    closing_date_name = fields.Char('Closing Date Name')
    start_day = fields.Char('Start Date')
    closing_date_circle = fields.Char('Closing Date Circle')



