# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassIndustry(models.Model):
    _inherit = 'res.partner.industry'

    industry_code = fields.Char('Industry Code')
    active = fields.Boolean('Active', default=True)


