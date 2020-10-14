from odoo import models, fields
import jaconv



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

    def limit_chapter_reports(self, string_text=None):
        # string_text = jaconv.h2z(string_text, kana=True, digit=True, ascii=True).replace('\uff0d', '-').replace('\xa0', ' ').replace('\uff5e', '~')
        COUNT_REPLACE = '〇'
        string_text_tmp = string_text.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE)
        count = 0
        len_i = len(string_text)
        byte_count = 0
        while count < len_i and byte_count < 40:
            if len(string_text_tmp[count].encode('utf8')) > 1 and byte_count < 39:
                byte_count += 2
            else:
                byte_count += 1
            count += 1
        len_string = string_text[:count]
        return len_string

    def limit_number_field(self, number=0.00, number_len=20):
        if len(str(number)) > number_len:
            number = str(number)[:number_len]
        return float(number)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def limit_charater_field(self, string_text=None, text_len=20, name=False, first1=True):
        text_len = text_len*2
        len_string = ''
        COUNT_REPLACE = '〇'
        if string_text:
            # string_text = jaconv.h2z(string_text, kana=True, digit=True, ascii=True).replace('\uff0d', '-').replace('\xa0', ' ').replace('\uff5e', '~')
            if name:
                string_text1 = ''
                string_text2 = ''
                if len(string_text.splitlines()) - 1:
                    string_text1 = string_text.splitlines()[0]
                    string_text2 = string_text.splitlines()[1]
                    string_text2_tmp = string_text2.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE)
                else:
                    string_text1 = string_text
                    string_text2 = ''
                string_text1_tmp = string_text1.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE)
                if first1:
                    count = 0
                    len_i = len(string_text1)
                    byte_count = 0
                    while count < len_i and byte_count < text_len:
                        if len(string_text1_tmp[count].encode('utf8')) > 1 and byte_count < text_len - 1:
                            byte_count += 2
                        else:
                            byte_count += 1
                        count += 1
                    len_string = string_text1[:count]
                    # len_string = string_text1[:text_len]
                else:
                    count = 0
                    len_i = len(string_text2)
                    byte_count = 0
                    while count < len_i and byte_count < text_len:
                        if len(string_text2_tmp[count].encode('utf8')) > 1 and byte_count < text_len - 1:
                            byte_count += 2
                        else:
                            byte_count += 1
                        count += 1
                    len_string = string_text2[:count]
            else:
                string_text_tmp = string_text.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE)
                count = 0
                len_i = len(string_text)
                byte_count = 0
                while count < len_i and byte_count < text_len:
                    if len(string_text_tmp[count].encode('utf8')) > 1 and byte_count < text_len - 1:
                        byte_count += 2
                    else:
                        byte_count += 1
                    count += 1
                len_string = string_text[:count]
        # return len_string
        return len_string
        # return len_string.replace('-', '－').replace(' ', '　').replace('~', '～')

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
