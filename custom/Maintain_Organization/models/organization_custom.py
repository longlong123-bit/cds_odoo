# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClassOrganizationCustom(models.Model):
    # _name = 'organization.custom'
    _inherit = 'res.company'

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id

    client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)
    # searchkey = fields.Char('searchkey')
    # name = fields.Char('name', required=True)
    # description =fields.Char('description')
    # active = fields.Boolean('isactive', default=True)


