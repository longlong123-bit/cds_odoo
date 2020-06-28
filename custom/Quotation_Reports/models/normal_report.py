from odoo import models, fields


class PrintSale(models.Model):
    _inherit = 'sale.order'

    # Preview report
    def preview_report(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Quotation_Reports.handover_report',
            'model': 'sale.order',
            'report_type': "qweb-html",
        }
