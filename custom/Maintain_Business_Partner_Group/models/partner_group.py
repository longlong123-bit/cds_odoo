# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassPartnerGroup(models.Model):
    _name = 'business.partner.group.custom'

    partner_group_code = fields.Char('Partner Group Code', required=True)
    name = fields.Char('name', required=True)
    description =fields.Char('description')
    active = fields.Boolean('isactive', default=True)


