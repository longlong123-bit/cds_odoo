from odoo import models, fields, api

class BmInvoice(models.Model):
    _inherit = 'account.move'

    billed_status = fields.Boolean()
