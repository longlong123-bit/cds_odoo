# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClientCustom(models.Model):
    _name = 'client.custom'

    search_key_client = fields.Char('searchkey', required=True)
    name = fields.Char('name', required=True)
    description =fields.Char('description')
    active = fields.Boolean('isactive', default=True)

    @api.model
    def create(self, vals):
            search_key_count = self.env['client.custom'].search_count(
                [('search_key_client', '=', vals['search_key_client'])])
            if search_key_count > 0:
                raise ValidationError(_('The Search Key has already been registered'))
            return super(ClientCustom, self).create(vals)

