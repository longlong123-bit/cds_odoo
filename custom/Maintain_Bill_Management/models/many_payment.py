from odoo import api, fields, models


class ManyPayment(models.Model):
    _inherit = "many.payment"

    history_payment = fields.Many2one(
        comodel_name='bill.info', string='History payment', store=False)
