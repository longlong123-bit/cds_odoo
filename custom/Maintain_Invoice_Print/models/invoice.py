from odoo import api, fields, models

class PrintInvoice(models.Model):
    _inherit = 'account.move'

    def _get_display_invoiced_date(self):
        for rec in self:
            rec.invoiced_date_year = rec.x_studio_date_invoiced.year
            rec.invoiced_date_month = rec.x_studio_date_invoiced.month
            rec.invoiced_date_day = rec.x_studio_date_invoiced.day

    invoiced_date_year = fields.Char(readonly=True, store=False, compute=_get_display_invoiced_date)
    invoiced_date_month = fields.Char(readonly=True, store=False)
    invoiced_date_day = fields.Char(readonly=True, store=False)

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