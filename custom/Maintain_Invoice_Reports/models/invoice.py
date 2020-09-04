from odoo import models
from custom.Maintain_Invoice_Remake.models.invoice_customer_custom import rounding


class InvoiceReports(models.Model):
    _inherit = 'account.move'

    def rounding_report(self, number, pre=0, type_rounding='round'):
        return rounding(number, pre, type_rounding)

    def subtotal_amount_tax(self, tax_rate=0):
        subtotal = 0
        for line in self.line_ids:
            if self.x_voucher_tax_transfer and (
                    line.tax_rate == tax_rate or (tax_rate == 0 and line.tax_rate != 10 and line.tax_rate != 8)):
                subtotal += line.line_amount
        return subtotal

    def amount_tax_total(self, tax_rate=0):
        subtotal = 0
        for re in self:
            for line in re.line_ids:
                if line.tax_rate == tax_rate or (tax_rate == 0 and line.tax_rate != 10 and line.tax_rate != 8):
                    if re.x_voucher_tax_transfer == 'foreign_tax':
                        subtotal += rounding(line.line_tax_amount, 0,
                                             re.partner_id.customer_tax_rounding)
                    elif re.x_voucher_tax_transfer == 'voucher':
                        subtotal += line.voucher_line_tax_amount
                        print('subtotal', subtotal, line.voucher_line_tax_amount)
                    elif re.x_voucher_tax_transfer == 'invoice':
                        subtotal += 0
                    else:
                        subtotal += 0
            if tax_rate == 0 and re.x_voucher_tax_transfer == 'custom_tax':
                subtotal += re.x_voucher_tax_amount
        return rounding(subtotal, 0, self.partner_id.customer_tax_rounding)
