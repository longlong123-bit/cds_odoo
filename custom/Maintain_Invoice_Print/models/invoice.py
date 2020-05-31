from odoo import api, fields, models

class PrintInvoice(models.Model):
    _inherit = 'account.move'

    def report_dialog(self):
        return {
            'type': ''
        }

    # Custom preview invoice
    def preview_invoice(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Maintain_Invoice_Print.report_invoice_format1',
            'model': 'account.move',
            'report_type': "qweb-html",
        }