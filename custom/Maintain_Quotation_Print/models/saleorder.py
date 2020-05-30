from odoo import models, fields

class PrintSale(models.Model):
    _inherit = 'sale.order'

    def _get_display_expected_date(self):
        for rec in self:
            rec.expected_date_year = rec.expected_date.year
            rec.expected_date_month = rec.expected_date.month
            rec.expected_date_day = rec.expected_date.day

    expected_date_year = fields.Char(readonly=True, store=False, compute=_get_display_expected_date)
    expected_date_month = fields.Char(readonly=True, store=False)
    expected_date_day = fields.Char(readonly=True, store=False)

    # Preview report
    def preview_report(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Maintain_Quotation_Print.report_format1',
            'model': 'sale.order',
            'report_type': "qweb-html",
        }