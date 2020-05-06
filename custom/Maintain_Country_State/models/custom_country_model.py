# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassCountryState(models.Model):
    _inherit = 'res.country.state'

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id

    def _get_default_organization_id(self):
        return self.env["res.company"].search([], limit=1, order='id').id

    searchkey = fields.Char('searchkey')
    client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)
    organization = fields.Many2one('res.company', required=True, default=_get_default_organization_id)
    country_id = fields.Many2one('res.country', string='Country', required=True,
                                 default=lambda self: self.env['res.country'].search([('code', '=', 'JP')]))
    active = fields.Boolean('Active', default=True)


