from odoo import models
from custom.Maintain_Invoice_Remake.models.invoice_customer_custom import rounding


class InvoiceReports(models.Model):
    _inherit = 'account.move'

    def rounding_report(self, number, pre=0, type_rounding='round'):
        return rounding(number, pre, type_rounding)
