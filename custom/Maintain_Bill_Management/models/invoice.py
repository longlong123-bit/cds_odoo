from odoo import models, fields, api

class BmInvoice(models.Model):
    _inherit = 'account.move'

    is_billed = fields.Boolean()