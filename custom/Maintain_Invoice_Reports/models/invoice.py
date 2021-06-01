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
        count = 0
        len_string = ''
        COUNT_REPLACE = '〇'
        if string_text:
            if name:
                string_text1 = ''
                string_text2 = ''
                if len(string_text.splitlines()) - 1:
                    string_text1 = string_text.splitlines()[0]
                    string_text2 = string_text.splitlines()[1]
                    string_text2_tmp = string_text2.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE)
                else:
                    string_text1 = string_text
                string_text1_tmp = string_text1.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE)
                if first1:
                    len_i = len(string_text1)
                    byte_count = 0
                    while count < len_i and byte_count < text_len:
                        try:
                            if len(string_text1_tmp[count].encode('shift_jisx0213')) > 1 and byte_count < text_len - 1:
                                byte_count += 2
                            else:
                                byte_count += 1
                        except:
                            byte_count += 2
                        count += 1
                    len_string = string_text1[:count]
                    # len_string = string_text1[:text_len]
                else:
                    len_i = len(string_text2)
                    byte_count = 0
                    while count < len_i and byte_count < text_len:
                        try:
                            if len(string_text2_tmp[count].encode('shift_jisx0213')) > 1 and byte_count < text_len - 1:
                                byte_count += 2
                            else:
                                byte_count += 1
                        except:
                            byte_count += 2
                        count += 1
                    len_string = string_text2[:count]
                    # len_string = string_text2[:text_len]
            else:
                if not first1 and len(string_text.splitlines()) - 1:
                    for i in string_text.splitlines():
                        string_text += i
                string_text_tmp = string_text.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE)
                len_i = len(string_text)
                byte_count = 0
                while count < len_i and byte_count < text_len:
                    try:
                        if len(string_text_tmp[count].encode('shift_jisx0213')) > 1 and byte_count < text_len - 1:
                            byte_count += 2
                        else:
                            byte_count += 1
                    except:
                        byte_count += 2
                    count += 1
                len_string = string_text[:count]
        return len_string

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

    def check_last_page(self, limit=0, voucher=False):
        self.ensure_one()
        if len(self.invoice_line_ids) % limit == 0 and voucher:
            return int(len(self.invoice_line_ids) / limit)
        elif voucher:
            return 0
        else:
            return int(len(self.invoice_line_ids) / limit) + 1

    def get_product_tax_category(self, product_code=''):
        sql = "select product_tax_category from product_product where barcode ='" + product_code + "'"
        self._cr.execute(sql)
        record = self._cr.dictfetchall()
        product_tax_category = record[0]['product_tax_category']
        return product_tax_category

    def get_marker_by_product_tax_category(self, product_code=''):
        marker = ''
        if self.get_product_tax_category(product_code) == 'internal':
            marker = '※'
        return marker
