from odoo import api, fields, models


class InvoiceReports(models.Model):
    _inherit = 'account.move'

    # Custom preview invoice
    def preview_invoice(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Maintain_Invoice_Reports.invoice_reports',
            'model': 'account.move',
            'report_type': "qweb-html",
        }
