from odoo import api, fields, models

class PrintInvoice(models.Model):
    _inherit = 'account.move'

    def report_dialog(self):
        return {
            'type': ''
        }