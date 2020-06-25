from odoo import models, fields
from datetime import datetime
from erajp.converter import strjpftime


class PrintSale(models.Model):
    _inherit = 'sale.order'

    # Preview report
    def preview_report(self):

        print(strjpftime(datetime.datetime(1989, 1, 8), u"%O%E年"))

        return {
            'type': 'ir.actions.report',
            'report_name': 'Quotation_Reports.handover_one',
            'model': 'sale.order',
            'report_type': "qweb-html",
        }
