from odoo import models
from custom.Maintain_Invoice_Remake.models.invoice_customer_custom import rounding
import jaconv


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

    def limit_charater_field(self, string_text=None, text_len=20, name=False, first1=True):
        len_string = ''
        string_text = jaconv.h2z(string_text, kana=True, digit=True, ascii=True).replace('\uff0d', '-').replace('\xa0', ' ').replace('\uff5e', '~')
        if name:
            string_text1 = ''
            string_text2 = ''
            if len(string_text.splitlines()) - 1:
                string_text1 = string_text.splitlines()[0]
                string_text2 = string_text.splitlines()[1]
            else:
                string_text1 = string_text
                string_text2 = ''
            if first1:
                len_string = string_text1[:text_len]
            else:
                len_string = string_text2[:text_len]
        else:
            if not first1 and len(string_text.splitlines()) - 1:
                for i in string_text.splitlines():
                    string_text += i
            len_string = string_text[:text_len]
        return len_string.replace('-', '－').replace(' ', '　').replace('~', '～')

    def limit_number_field(self, number=0.00, number_len=20, name=False):
        if name:
            if number % 1 > 0:
                number_len = number_len - 2
                number = str(int(number))[:number_len] + str(number % 1)[1:]
            else:
                number = str(number)[:number_len]
        else:
            if len(str(number)) > number_len:
                number = str(number)[:number_len]
        return float(number)
