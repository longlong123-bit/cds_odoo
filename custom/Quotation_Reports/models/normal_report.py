from odoo import models, fields
from datetime import datetime

# from erajp.converter import strjpftime


ERA_JP = (
    ("M", "明治"),
    ("T", "大正"),
    ("S", "昭和"),
    ("H", "平成"),
    ("R", "令和"),
)


class PrintSale(models.Model):
    _inherit = 'sale.order'

    # Preview report
    def preview_report(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Quotation_Reports.handover_one',
            'model': 'sale.order',
            'report_type': "qweb-html",
        }
