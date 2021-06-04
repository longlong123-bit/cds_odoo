from odoo import api, fields, models
# from datetime import date
from datetime import date, timedelta
from odoo.tools.float_utils import float_round
from . import payment_request_bill
import calendar
import jaconv
import time

def rounding(number, pre=0, type_rounding='round'):
    """Rounding number by type rounding(round, roundup, rounddown)."""
    if number != 0:
        if type_rounding == 'roundup':
            return float_round(number, pre, None, 'UP')
        elif type_rounding == 'rounddown':
            return float_round(number, pre, None, 'DOWN')
        else:
            return float_round(number, pre)
    else:
        return 0


class PrintPaymentRequest(models.Model):
    _inherit = 'bill.invoice'

    last_billed_amount = fields.Monetary(string='Last Billed Amount', currency_field='currency_id')
    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id')
    balance_amount = fields.Monetary(string='Balance Amount', currency_field='currency_id')
    tax_amount = fields.Monetary(string='Tax Amount', currency_field='currency_id')
    customer_other_cd = fields.Char('Customer CD', readonly=True)
    invoices_number = fields.Integer(string='Number of Invoices', default=0)
    # con.

    bill_user_id = fields.Many2one('res.users', copy=False, tracking=True,
                                   string='Salesperson',
                                   default=lambda self: self.env.user)


class BillInvoiceDetail(models.Model):
    _inherit = 'bill.invoice.details'

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

    # Limit Character and Number:
    def limit_charater_field(self, string_text=None, text_len=20, name=False, first1=True):
        text_len = text_len * 2
        count = 0
        len_string = ''
        COUNT_REPLACE = '〇'
        a = ' '
        if string_text:
            # string_text = jaconv.h2z(string_text, kana=True, digit=True, ascii=True).replace('\uff0d', '-').replace('\xa0', ' ').replace('\uff5e', '~')
            if name:
                string_text1 = ''
                string_text2 = ''
                if len(string_text.splitlines()) - 1:
                    string_text1 = string_text.splitlines()[0]
                    string_text2 = string_text.splitlines()[1]
                    string_text2_tmp = string_text2.replace('\uff0d', COUNT_REPLACE).replace('\xa0',
                                                                                             COUNT_REPLACE).replace(
                        '\uff5e', COUNT_REPLACE).replace(' ', 'a')

                else:
                    string_text1 = string_text
                    string_text2 = ''
                    string_text1_tmp = string_text1.replace('\uff0d', COUNT_REPLACE).replace('\xa0',
                                                                                             COUNT_REPLACE).replace(
                        '\uff5e', COUNT_REPLACE).replace(' ', 'a')
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
                    count = 0
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
            else:
                if not first1 and len(string_text.splitlines()) - 1:
                    for i in string_text.splitlines():
                        string_text += string_text.splitlines()[i]
                string_text_tmp = string_text.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace(
                    '\uff5e', COUNT_REPLACE).replace(' ', 'a')
                count = 0
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

    def record_data(self):
        return self

    def count_detail_line(self):
        self.ensure_one()
        count_detail = 1
        count = len(self.product_name.splitlines()) - 1
        if self.tax_rate == 8 or self.account_move_line_id.product_id.product_tax_category == 'exempt':
            count_detail += 1
        if count > 0:
            count_detail += 1
        if self.payment_id.comment_apply:
            count_detail += 1
        if self.product_maker_name and self.product_custom_standardnumber and self.limit_charater_field(self.product_name, 20, True, False) == '':
            count_detail += 1
        return count_detail

    def gross_maker_and_standard(self):
        self.ensure_one()
        gross = ''
        if self.product_maker_name and self.product_custom_standardnumber:
            gross = str(self.product_custom_standardnumber) + ' ' + str(self.product_maker_name)
        elif self.product_maker_name and not self.product_custom_standardnumber:
            gross = str(self.product_maker_name)
        else:
            gross = self.product_custom_standardnumber
        len_string = ''
        count = 0
        if gross:
            COUNT_REPLACE = '〇'
            string_text = gross.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE).replace(' ', 'a')
            len_i = len(gross)
            byte_count = 0
            while count < len_i and byte_count < 20:
                try:
                    if len(string_text[count].encode('shift_jisx0213')) > 1 and byte_count < 19:
                        byte_count += 2
                    else:
                        byte_count += 1
                except:
                    byte_count += 2
                count += 1
            len_string = gross[:count]
        return len_string


class BillInfoGet(models.Model):
    _inherit = 'bill.info'

    def _get_customer_other_cd(self):
        for cd in self:
            # if self.partner_id:
            cd.customer_other_cd = cd.partner_id.customer_other_cd

    # その他CD
    customer_other_cd = fields.Char('Customer CD', readonly=True, compute='_get_customer_other_cd')

    def preview_invoice(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Maintain_Payment_Request_Bill.reports',
            'model': 'bill.info',
            'report_type': "qweb-pdf",
        }

    def subtotal_amount_tax(self, tax_rate=0):
        subtotal = 0
        _tax = 0
        for line in self.bill_detail_ids:
            if line.x_voucher_tax_transfer and (
                    line.tax_rate == tax_rate or (tax_rate == 0 and line.tax_rate != 10 and line.tax_rate != 8)):
                subtotal += line.line_amount
                if line.account_move_line_id.product_id.product_tax_category == 'internal' or line.account_move_line_id.move_id.x_voucher_tax_transfer == 'internal_tax':
                    _tax = line.account_move_line_id.invoice_custom_lineamount * line.account_move_line_id.product_id.product_tax_rate / (
                                100 + line.account_move_line_id.product_id.product_tax_rate)
                    _tax = rounding(_tax, 0, line.account_move_line_id.move_id.customer_tax_rounding)
                    subtotal -= _tax
        return subtotal

    def amount_tax(self, tax_rate=0):
        subtotal = 0
        for re in self.bill_invoice_ids:
            for line in re.bill_invoice_details_ids:
                if line.tax_rate == tax_rate or (tax_rate == 0 and line.tax_rate != 10 and line.tax_rate != 8):
                    if line.x_voucher_tax_transfer == 'foreign_tax':
                        subtotal += rounding(line.tax_amount, 0,
                                             line.account_move_line_id.move_id.customer_tax_rounding)
                    elif line.x_voucher_tax_transfer == 'voucher':
                        subtotal += line.voucher_line_tax_amount
                    elif line.x_voucher_tax_transfer == 'invoice':
                        subtotal += line.line_amount * line.tax_rate / 100
            if tax_rate == 0 and re.x_voucher_tax_transfer == 'custom_tax':
                subtotal += re.amount_tax
        return rounding(subtotal, 0, self.partner_id.customer_tax_rounding)

    def subtotal_amount_tax_child(self, tax_rate=0, customer_code=None):
        subtotal = 0
        _tax = 0
        for line in self.bill_detail_ids:
            if line.customer_code == customer_code:
                if line.x_voucher_tax_transfer and (
                        line.tax_rate == tax_rate or (tax_rate == 0 and line.tax_rate != 10 and line.tax_rate != 8)):
                    subtotal += line.line_amount
                    if line.account_move_line_id.product_id.product_tax_category == 'internal' or line.account_move_line_id.move_id.x_voucher_tax_transfer == 'internal_tax':
                        _tax = line.account_move_line_id.invoice_custom_lineamount * line.account_move_line_id.product_id.product_tax_rate / (
                                100 + line.account_move_line_id.product_id.product_tax_rate)
                        _tax = rounding(_tax, 0, line.account_move_line_id.move_id.customer_tax_rounding)
                        subtotal -= _tax
                else:
                    subtotal += 0
        return subtotal

    def amount_for_customer(self, customer_code=None):
        amount = 0
        for line in self.bill_invoice_ids:
            if line.customer_code == customer_code:
                amount += line.amount_total
            else:
                amount += 0
        return amount

    def amount_tax_child(self, tax_rate=0, customer_code=None):
        subtotal = 0
        _tax = 0
        for re in self.bill_invoice_ids:
            if re.customer_code == customer_code:
                for line in re.bill_invoice_details_ids:
                    if line.tax_rate == tax_rate or (tax_rate == 0 and line.tax_rate != 10 and line.tax_rate != 8):
                        if line.x_voucher_tax_transfer == 'foreign_tax':
                            subtotal += rounding(line.tax_amount, 0,
                                                 line.account_move_line_id.move_id.customer_tax_rounding)
                        elif line.x_voucher_tax_transfer == 'voucher':
                            subtotal += line.voucher_line_tax_amount
                        elif line.x_voucher_tax_transfer == 'invoice':
                            subtotal += line.line_amount * line.tax_rate / 100
                        if line.account_move_line_id.product_id.product_tax_category == 'internal' or line.account_move_line_id.move_id.x_voucher_tax_transfer == 'internal_tax':
                            _tax = line.account_move_line_id.invoice_custom_lineamount * line.account_move_line_id.product_id.product_tax_rate / (
                                    100 + line.account_move_line_id.product_id.product_tax_rate)
                            _tax = rounding(_tax, 0, line.account_move_line_id.move_id.customer_tax_rounding)
                            subtotal += _tax
                    if tax_rate == 0 and line.x_voucher_tax_transfer == 'custom_tax':
                        subtotal += re.amount_tax
                    else:
                        subtotal += 0
        return rounding(subtotal, 0, self.partner_id.customer_tax_rounding)

    def count_customer_in_bill(self):
        arr = []
        for record in self.bill_invoice_ids:
            if record.customer_code not in arr:
                arr.append(record.customer_code)
        return len(arr)

    def count_detail_line(self):
        count_line = 0
        for record in self.bill_detail_ids:
            count_line += record.count_detail_line()
        return count_line

    #TH - viet lai report payment_request_bill
    def record_data(self):
        a = []
        bill_detail_list = self.bill_detail_ids
        record_data_list = sorted(self.bill_detail_ids, key=lambda bill_detail_list: (bill_detail_list.invoice_date, bill_detail_list.invoice_no, bill_detail_list.account_move_line_id.invoice_custom_line_no))
        invoice_no_before = 0
        record_final = 0
        payment_id_before = 0
        for record in record_data_list:
            type_product = record.account_move_line_id.product_id.product_tax_category
            check_two_line = 0
            # Gan gia tri
            quantity_convert = '{0:,.0f}'.format(self.limit_number_field(int(record.quantity), 7))
            price_unit_convert = '{0:,.0f}'.format(self.limit_number_field(record.price_unit, 8))
            price_unit_convert_2 = '{0:,.2f}'.format(record.limit_number_field(record.price_unit, 8), True)
            product_uom_convert = record.limit_charater_field(record.product_uom, 2)
            invoice_date_convert = record.invoice_date.strftime("%y/%m/%d")
            line_amount_convert = '{0:,.0f}'.format(record.limit_number_field(int(record.line_amount), 8))
            amount_tax_convert = '{0:,.0f}'.format(self.limit_number_field(int(record.bill_invoice_id.amount_tax), 11))
            # In gia tri dau tien cho report
            if len(a) == 0:
                if record.account_move_line_id:
                    #Check truong hop invoice la internal_tax
                    if record.x_voucher_tax_transfer == 'internal_tax':
                        if record.price_unit % 1 > 0:
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 20, True), record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 20, True), record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False), record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '', '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        if record.price_unit % 1 == 0:
                            # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 20, True), record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 20, True), record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False), record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '', '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                    else:
                        if record.price_unit % 1 > 0:
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                         '', '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        if record.price_unit % 1 == 0:
                            # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                         '', '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                else:
                    account_payment_line_ids = record.env['account.payment.line'].search(
                        [('payment_id', 'in', record.payment_id.ids)])
                    count = 0
                    for account_payment_line in account_payment_line_ids:
                        payment_category_name = account_payment_line.receipt_divide_custom_id.name
                        payment_line_amount = '{0:,.0f}'.format(
                            record.limit_number_field(int(account_payment_line.payment_amount), 8))
                        if count == 0:
                            a.append(
                                [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                 '', '', '', '', payment_line_amount, check_two_line])
                        else:
                            a.append(
                                ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                 '', '', '', '', payment_line_amount, check_two_line])
                        count += 1
                    if record.payment_id.comment_apply:
                        a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                  '', '', '', '', '', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                invoice_no_before = record.invoice_no
                payment_id_before = record.payment_id.id
                record_final = record
            # Check invoice_no de in thue va tong khi het 1 invoice_no (co 2 dong cach)
            elif record.invoice_no != invoice_no_before:
                #Check cac truong hop co ARR
                if payment_id_before == False and record.payment_id.id:
                    if record_final.x_voucher_tax_transfer == 'foreign_tax' or record_final.x_voucher_tax_transfer == 'voucher':
                        a.append(['', '', '消費税', '', '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(record_final.bill_invoice_id.amount_tax), 11)), check_two_line])
                    if record_final.bill_invoice_id.x_studio_summary:
                        a.append(['', '', '＜' + self.limit_charater_field(record_final.bill_invoice_id.x_studio_summary, 12) + '＞', '', '', '', '', '(' + str('{0:,.0f}'.format(
                        self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    else:
                        a.append(['', '', '', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert], check_two_line)
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert], check_two_line)
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search([('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    payment_id_before = record.payment_id.id
                    record_final = record
                # Check cac truong hop co ARR
                elif payment_id_before and record.payment_id.id:
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    payment_id_before = record.payment_id.id
                    record_final = record
                # Check cac truong hop co ARR
                elif payment_id_before and record.payment_id.id == False:
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    payment_id_before = record.payment_id.id
                    record_final = record
                #In thue binh thuong khong tinh ARR
                else:
                    if record_final.x_voucher_tax_transfer == 'foreign_tax' or record_final.x_voucher_tax_transfer == 'voucher':
                        a.append(['', '', '消費税', '', '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_tax), 11)), check_two_line])
                    if record_final.bill_invoice_id.x_studio_summary:
                        a.append(['', '', '＜' + self.limit_charater_field(record_final.bill_invoice_id.x_studio_summary, 12) + '＞', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    else:
                        a.append(['', '', '', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    payment_id_before = record.payment_id.id
                    record_final = record
            # In invoice nhung dong o giua
            else:
                if record.account_move_line_id:
                    if record.x_voucher_tax_transfer == 'internal_tax':
                        if record.price_unit % 1 > 0:
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 20, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 20, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                         '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        if record.price_unit % 1 == 0:
                            # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 20, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 20, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                         '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                    else:
                        if record.price_unit % 1 > 0:
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                         '',
                                         '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        if record.price_unit % 1 == 0:
                            # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                         '',
                                         '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                else:
                    account_payment_line_ids = record.env['account.payment.line'].search(
                        [('payment_id', 'in', record.payment_id.ids)])
                    count = 0
                    for account_payment_line in account_payment_line_ids:
                        payment_category_name = account_payment_line.receipt_divide_custom_id.name
                        payment_line_amount = '{0:,.0f}'.format(
                            record.limit_number_field(int(account_payment_line.payment_amount), 8))
                        if count == 0:
                            a.append(
                                [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                 '', '', '', '', payment_line_amount, check_two_line])
                        else:
                            a.append(
                                ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                 '', '', '', '', payment_line_amount, check_two_line])
                        count += 1
                    if record.payment_id.comment_apply:
                        a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                  '', '', '', '', '', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                invoice_no_before = record.invoice_no
                payment_id_before = record.payment_id.id
                record_final = record
        if len(a) != 0:
            check_two_line = 0
            amount_tax_convert = '{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_tax), 11))
            amount_total_bill_convert = '{0:,.0f}'.format(self.limit_number_field(int(self.amount_total), 8))
            subtotal_amount_tax_10 = '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax(10)), 11))
            subtotal_amount_tax_8 = '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax(8)), 11))
            subtotal_amount_tax_0 = '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax()), 11))
            # Check hang cuoi cung la invoice hay payment
            if record_final.bill_invoice_id:
                if record_final.x_voucher_tax_transfer == 'foreign_tax' or record_final.x_voucher_tax_transfer == 'voucher':
                    a.append(
                        ['', '', '消費税', '', '', '', '', amount_tax_convert, check_two_line])
                if record_final.bill_invoice_id.x_studio_summary:
                    a.append(['', '', '＜' + self.limit_charater_field(record_final.bill_invoice_id.x_studio_summary, 12) + '＞', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                else:
                    a.append(['', '', '', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
            a.append(['', '', '', '', '', '', '', '', check_two_line])
            if self.partner_id.customer_tax_unit == 'invoice':
                a.append(['', '', '（税別御買上計）　　　　　（10％対象）', '',
                          '', '', '', subtotal_amount_tax_10, check_two_line])
                a.append(['', '', '　　　　　　　　　　　　　（8％対象）', '',
                          '', '', '', subtotal_amount_tax_8, check_two_line])
                if self.subtotal_amount_tax():
                    a.append(['', '', '', '', '', '', '', subtotal_amount_tax_0, check_two_line])
                if self.amount_tax(8):
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.tax_amount - self.amount_tax(8) - self.amount_tax()), 11)), check_two_line])
                    a.append(['', '','　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '',
                              '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax(8)), 11)), check_two_line])
                else:
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.tax_amount - self.amount_tax()), 11)), check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax(8)), 11)), check_two_line])
                if self.amount_tax():
                    a.append(['', '', '', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax()), 11)), check_two_line])
            else:
                a.append(['', '', '【　合　　計　】', '', '', '', '', amount_total_bill_convert, check_two_line])
                a.append(['', '', '（税別御買上計）　　　　　（10％対象）', '',
                          '', '', '', subtotal_amount_tax_10, check_two_line])
                a.append(['', '', '　　　　　　　　　　　　　（8％対象）', '',
                          '', '', '', subtotal_amount_tax_8, check_two_line])
                if self.subtotal_amount_tax():
                    a.append(['', '', '', '', '', '', '', subtotal_amount_tax_0, check_two_line])
                if self.amount_tax(8):
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.tax_amount - self.amount_tax(8) - self.amount_tax()), 11)), check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '',
                              '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax(8)), 11)), check_two_line])
                else:
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.tax_amount - self.amount_tax()), 11)), check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax(8)), 11)), check_two_line])
                if self.amount_tax():
                    a.append(['', '', '', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax()), 11)), check_two_line])
        if a == []:
            a.append(['', '', '', '', '', '', '', '', 0])
        return a
    #TH - done

    def record_data_special_bill(self):
        a = []
        bill_detail_list = self.bill_detail_ids
        record_data_list = sorted(self.bill_detail_ids, key=lambda bill_detail_list: (bill_detail_list.flag_child_billing_code, bill_detail_list.invoice_date,
                                                                                      bill_detail_list.invoice_no, bill_detail_list.account_move_line_id.invoice_custom_line_no))
        invoice_no_before = 0
        record_final = 0
        payment_id_before = 0
        customer_code_child_before = 0
        for record in record_data_list:
            type_product = record.account_move_line_id.product_id.product_tax_category
            check_two_line = 0
            # Gan gia tri
            quantity_convert = '{0:,.0f}'.format(self.limit_number_field(int(record.quantity), 7))
            price_unit_convert = '{0:,.0f}'.format(self.limit_number_field(record.price_unit, 8))
            price_unit_convert_2 = '{0:,.2f}'.format(record.limit_number_field(record.price_unit, 8), True)
            product_uom_convert = record.limit_charater_field(record.product_uom, 2)
            invoice_date_convert = record.invoice_date.strftime("%y/%m/%d")
            line_amount_convert = '{0:,.0f}'.format(record.limit_number_field(int(record.line_amount), 8))
            amount_tax_convert = '{0:,.0f}'.format(self.limit_number_field(int(record.bill_invoice_id.amount_tax), 11))
            # In gia tri dau tien cho report
            customer_code_child = record.customer_code
            if len(a) == 0:
                if record.account_move_line_id:
                    #Check truong hop invoice la internal_tax
                    if record.x_voucher_tax_transfer == 'internal_tax':
                        if record.price_unit % 1 > 0:
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 20, True), record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 20, True), record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False), record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '', '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        if record.price_unit % 1 == 0:
                            # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 20, True), record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append([invoice_date_convert, record.invoice_no,
                                              record.limit_charater_field(record.product_name, 20, True), record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False), record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '', '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                    else:
                        if record.price_unit % 1 > 0:
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                         '', '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        if record.price_unit % 1 == 0:
                            # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                         '', '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                else:
                    account_payment_line_ids = record.env['account.payment.line'].search(
                        [('payment_id', 'in', record.payment_id.ids)])
                    count = 0
                    for account_payment_line in account_payment_line_ids:
                        payment_category_name = account_payment_line.receipt_divide_custom_id.name
                        payment_line_amount = '{0:,.0f}'.format(
                            record.limit_number_field(int(account_payment_line.payment_amount), 8))
                        if count == 0:
                            a.append(
                                [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                 '', '', '', '', payment_line_amount, check_two_line])
                        else:
                            a.append(
                                ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                 '', '', '', '', payment_line_amount, check_two_line])
                        count += 1
                    if record.payment_id.comment_apply:
                        a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                  '', '', '', '', '', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                invoice_no_before = record.invoice_no
                payment_id_before = record.payment_id.id
                customer_code_child_before = record.customer_code
                record_final = record
            # Check invoice_no de in thue va tong khi het 1 invoice_no (co 2 dong cach)
            elif record.invoice_no != invoice_no_before and record.customer_code == record_final.customer_code:
                #Check cac truong hop co ARR
                if payment_id_before == False and record.payment_id.id:
                    if record_final.x_voucher_tax_transfer == 'foreign_tax' or record_final.x_voucher_tax_transfer == 'voucher':
                        a.append(['', '', '消費税', '', '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(record_final.bill_invoice_id.amount_tax), 11)), check_two_line])
                    if record_final.bill_invoice_id.x_studio_summary:
                        a.append(['', '', '＜' + self.limit_charater_field(record_final.bill_invoice_id.x_studio_summary, 12) + '＞'
                                 , '', '', '', '', '(' + str('{0:,.0f}'.format(
                        self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    else:
                        a.append(['', '', '', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert], check_two_line)
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert], check_two_line)
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search([('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    customer_code_child_before = record.customer_code
                    payment_id_before = record.payment_id.id
                    record_final = record
                    customer_code_child_final = record.customer_code
                # Check cac truong hop co ARR
                elif payment_id_before and record.payment_id.id:
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    customer_code_child_before = record.customer_code
                    payment_id_before = record.payment_id.id
                    record_final = record
                    customer_code_child_final = record.customer_code
                # Check cac truong hop co ARR
                elif payment_id_before and record.payment_id.id == False:
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    customer_code_child_before = record.customer_code
                    payment_id_before = record.payment_id.id
                    record_final = record
                    customer_code_child_final = record.customer_code
                #In thue binh thuong khong tinh ARR
                else:
                    if record_final.x_voucher_tax_transfer == 'foreign_tax' or record_final.x_voucher_tax_transfer == 'voucher':
                        a.append(['', '', '消費税', '', '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_tax), 11)), check_two_line])
                    if record_final.bill_invoice_id.x_studio_summary:
                        a.append(['', '', '＜' + self.limit_charater_field(record_final.bill_invoice_id.x_studio_summary, 12) + '＞', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    else:
                        a.append(['', '', '', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    customer_code_child_before = record.customer_code
                    payment_id_before = record.payment_id.id
                    record_final = record
        #Truong hop thay doi customer_code
            elif record.invoice_no != invoice_no_before and record.customer_code != record_final.customer_code:
                check_two_line = 0
                # Check hang cuoi cung la invoice hay payment
                if self.partner_id.customer_tax_unit == 'invoice':
                    a.append(['', '', '（税別御買上計）　　　　　（10％対象）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax_child(10, record_final.customer_code)), 11)), check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％対象）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax_child(8, record_final.customer_code)), 11)), check_two_line])
                    if self.subtotal_amount_tax_child(0, record_final.customer_code):
                        a.append(['', '', '', '', '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax_child(0, record_final.customer_code)), 11)), check_two_line])
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                                  '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax_child(10, record_final.customer_code)), 11)), check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax_child(8, record_final.customer_code)), 11)), check_two_line])
                    if self.amount_tax_child(0, record_final.customer_code):
                        a.append(['', '', '', '', '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax_child(0, record_final.customer_code)), 11)), check_two_line])
                    a.append(['', '', '【　合　　計　】', '', '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 11)),
                              check_two_line])
                else:
                    a.append(['', '', '【　合　　計　】', '', '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_for_customer(record_final.customer_code)), 11)), check_two_line])
                    a.append(['', '', '（税別御買上計）　　　　　（10％対象）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax_child(10, record_final.customer_code)),11)), check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％対象）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax_child(8, record_final.customer_code)),11)), check_two_line])
                    if self.subtotal_amount_tax_child(0, record_final.customer_code):
                        a.append(['', '', '', '', '', '', '', '{0:,.0f}'.format(
                            self.limit_number_field(int(self.subtotal_amount_tax_child(0, record_final.customer_code)),
                                                    11)), check_two_line])
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(
                            self.limit_number_field(int(self.amount_tax_child(10, record_final.customer_code)), 11)),
                              check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(
                            self.limit_number_field(int(self.amount_tax_child(8, record_final.customer_code)), 11)),
                              check_two_line])
                    if self.amount_tax_child(0, record_final.customer_code):
                        a.append(['', '', '', '', '', '', '', '{0:,.0f}'.format(
                            self.limit_number_field(int(self.amount_tax_child(0, record_final.customer_code)), 11)),
                                  check_two_line])
                a.append(['', '', '', '', '', '', '', '', 4])
                a.append(['', '', '得意先コード　　　　　　　　　' + str(record.customer_code), '', '', '', '', '', check_two_line])
                a.append(['', '', '得意先名　　　　　　　　　　　' + str(record.customer_name), '', '', '', '', '', check_two_line])
                #Check cac truong hop co ARR
                if payment_id_before == False and record.payment_id.id:
                    if record_final.x_voucher_tax_transfer == 'foreign_tax' or record_final.x_voucher_tax_transfer == 'voucher':
                        a.append(['', '', '消費税', '', '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(record_final.bill_invoice_id.amount_tax), 11)), check_two_line])
                    if record_final.bill_invoice_id.x_studio_summary:
                        a.append(['', '', '＜' + self.limit_charater_field(record_final.bill_invoice_id.x_studio_summary, 12) + '＞', '', '', '', '', '(' + str('{0:,.0f}'.format(
                        self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    else:
                        a.append(['', '', '', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert], check_two_line)
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert], check_two_line)
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search([('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    customer_code_child_before = record.customer_code
                    payment_id_before = record.payment_id.id
                    record_final = record
                    customer_code_child_final = record.customer_code
                # Check cac truong hop co ARR
                elif payment_id_before and record.payment_id.id:
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '',
                                             '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    customer_code_child_before = record.customer_code
                    payment_id_before = record.payment_id.id
                    record_final = record
                    customer_code_child_final = record.customer_code
                # Check cac truong hop co ARR
                elif payment_id_before and record.payment_id.id == False:
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    customer_code_child_before = record.customer_code
                    payment_id_before = record.payment_id.id
                    record_final = record
                    customer_code_child_final = record.customer_code
                #In thue binh thuong khong tinh ARR
                else:
                    if record_final.x_voucher_tax_transfer == 'foreign_tax' or record_final.x_voucher_tax_transfer == 'voucher':
                        a.append(['', '', '消費税', '', '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_tax), 11)), check_two_line])
                    if record_final.bill_invoice_id.x_studio_summary:
                        a.append(['', '', '＜' + self.limit_charater_field(record_final.bill_invoice_id.x_studio_summary, 12) + '＞', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    else:
                        a.append(['', '', '', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                    if record.account_move_line_id:
                        if record.x_voucher_tax_transfer == 'internal_tax':
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([invoice_date_convert, record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                                  record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        else:
                            if record.price_unit % 1 > 0:
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert_2) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert_2,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                            if record.price_unit % 1 == 0:
                                # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                                if record.product_maker_name == False and record.product_custom_standardnumber:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([invoice_date_convert, record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_custom_standardnumber,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                else:
                                    if not record.limit_charater_field(record.product_name, 20, True, False):
                                        check_two_line = 1
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 18, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                    else:
                                        if type_product == 'internal':
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      str(price_unit_convert) + '※',
                                                      line_amount_convert, check_two_line])
                                        else:
                                            a.append([record.invoice_date.strftime("%y/%m/%d"), record.invoice_no,
                                                      record.limit_charater_field(record.product_name, 20, True),
                                                      record.product_maker_name,
                                                      quantity_convert, product_uom_convert,
                                                      price_unit_convert,
                                                      line_amount_convert, check_two_line])
                                # In dong thu 2
                                if record.limit_charater_field(record.product_name, 20, True, False) or (
                                        record.product_maker_name and record.product_custom_standardnumber):
                                    if record.product_maker_name and record.product_custom_standardnumber:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             record.product_custom_standardnumber, '', '', '', '', 2])
                                    else:
                                        a.append(
                                            ['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                             '', '',
                                             '', '', '', 2])
                                # In dong thu 3
                                if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    if record.tax_rate == 8:
                                        a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                    elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                        a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                    else:
                        account_payment_line_ids = record.env['account.payment.line'].search(
                            [('payment_id', 'in', record.payment_id.ids)])
                        count = 0
                        for account_payment_line in account_payment_line_ids:
                            payment_category_name = account_payment_line.receipt_divide_custom_id.name
                            payment_line_amount = '{0:,.0f}'.format(
                                record.limit_number_field(int(account_payment_line.payment_amount), 8))
                            if count == 0:
                                a.append(
                                    [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            else:
                                a.append(
                                    ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                     '', '', '', '', payment_line_amount, check_two_line])
                            count += 1
                        if record.payment_id.comment_apply:
                            a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                      '', '', '', '', '', check_two_line])
                        a.append(['', '', '', '', '', '', '', '', check_two_line])
                    invoice_no_before = record.invoice_no
                    customer_code_child_before = record.customer_code
                    payment_id_before = record.payment_id.id
                    record_final = record
            # In invoice nhung dong o giua
            else:
                if record.account_move_line_id:
                    if record.x_voucher_tax_transfer == 'internal_tax':
                        if record.price_unit % 1 > 0:
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 20, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 20, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert_2) + '※',
                                              line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                         '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        if record.price_unit % 1 == 0:
                            # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 20, True),
                                              record.product_custom_standardnumber,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 18, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                                else:
                                    a.append(['', '',
                                              record.limit_charater_field(record.product_name, 20, True),
                                              record.product_maker_name,
                                              quantity_convert, product_uom_convert,
                                              str(price_unit_convert) + '※',
                                              line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '', '',
                                         '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                    else:
                        if record.price_unit % 1 > 0:
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert_2) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert_2,
                                                  line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                         '',
                                         '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])
                        if record.price_unit % 1 == 0:
                            # In dong dau truong hop co product_maker_name hay khong. Neu khong co product_maker_name, dong 1 hien thi product_custom_standardnumber
                            if record.product_maker_name == False and record.product_custom_standardnumber:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_custom_standardnumber,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                            else:
                                if not record.limit_charater_field(record.product_name, 20, True, False):
                                    check_two_line = 1
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 18, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                                else:
                                    if type_product == 'internal':
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  str(price_unit_convert) + '※',
                                                  line_amount_convert, check_two_line])
                                    else:
                                        a.append(['', '',
                                                  record.limit_charater_field(record.product_name, 20, True),
                                                  record.product_maker_name,
                                                  quantity_convert, product_uom_convert,
                                                  price_unit_convert,
                                                  line_amount_convert, check_two_line])
                            # In dong thu 2
                            if record.limit_charater_field(record.product_name, 20, True, False) or (
                                    record.product_maker_name and record.product_custom_standardnumber):
                                if record.product_maker_name and record.product_custom_standardnumber:
                                    a.append(['', '', self.limit_charater_field(record.product_name, 20, True, False),
                                              record.product_custom_standardnumber, '', '', '', '', 2])
                                else:
                                    a.append(
                                        ['', '', self.limit_charater_field(record.product_name, 20, True, False), '',
                                         '',
                                         '', '', '', 2])
                            # In dong thu 3
                            if record.tax_rate == 8 or record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                if record.tax_rate == 8:
                                    a.append(['', '', '※軽減税率', '', '', '', '', '', check_two_line])
                                elif record.account_move_line_id.product_id.product_tax_category == 'exempt':
                                    a.append(['', '', '※非課税', '', '', '', '', '', check_two_line])

                else:
                    account_payment_line_ids = record.env['account.payment.line'].search(
                        [('payment_id', 'in', record.payment_id.ids)])
                    count = 0
                    for account_payment_line in account_payment_line_ids:
                        payment_category_name = account_payment_line.receipt_divide_custom_id.name
                        payment_line_amount = '{0:,.0f}'.format(
                            record.limit_number_field(int(account_payment_line.payment_amount), 8))
                        if count == 0:
                            a.append(
                                [invoice_date_convert, record.invoice_no, '【入金　（ ' + payment_category_name + ' ）】',
                                 '', '', '', '', payment_line_amount, check_two_line])
                        else:
                            a.append(
                                ['', '', '【入金　（ ' + payment_category_name + ' ）】',
                                 '', '', '', '', payment_line_amount, check_two_line])
                        count += 1
                    if record.payment_id.comment_apply:
                        a.append(['', '', self.limit_charater_field(record.payment_id.comment_apply, 30),
                                  '', '', '', '', '', check_two_line])
                    a.append(['', '', '', '', '', '', '', '', check_two_line])
                invoice_no_before = record.invoice_no
                payment_id_before = record.payment_id.id
                record_final = record
        if len(a) != 0:
            check_two_line = 0
            # Check hang cuoi cung la invoice hay payment
            if self.partner_id.customer_tax_unit == 'invoice':
                a.append(['', '', '（税別御買上計）　　　　　（10％対象）', '',
                          '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.subtotal_amount_tax_child(10, record_final.customer_code)),
                                                11)), check_two_line])
                a.append(['', '', '　　　　　　　　　　　　　（8％対象）', '',
                          '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.subtotal_amount_tax_child(8, record_final.customer_code)),
                                                11)), check_two_line])
                if self.subtotal_amount_tax_child(0, record_final.customer_code):
                    a.append(['', '', '', '', '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.subtotal_amount_tax_child(0, record_final.customer_code)),
                                                11)), check_two_line])
                a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                          '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.amount_tax_child(10, record_final.customer_code)), 11)),
                          check_two_line])
                a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                          '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.amount_tax_child(8, record_final.customer_code)), 11)),
                          check_two_line])
                if self.amount_tax_child(0, record_final.customer_code):
                    a.append(['', '', '', '', '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.amount_tax_child(0, record_final.customer_code)), 11)),
                              check_two_line])
                a.append(['', '', '【　合　　計　】', '', '', '', '', '{0:,.0f}'.format(
                    self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 11)),
                          check_two_line])
            else:
                a.append(['', '', '【　合　　計　】', '', '', '', '', '{0:,.0f}'.format(
                    self.limit_number_field(int(self.amount_for_customer(record_final.customer_code)), 11)),
                          check_two_line])
                a.append(['', '', '（税別御買上計）　　　　　（10％対象）', '',
                          '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.subtotal_amount_tax_child(10, record_final.customer_code)),
                                                11)), check_two_line])
                a.append(['', '', '　　　　　　　　　　　　　（8％対象）', '',
                          '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.subtotal_amount_tax_child(8, record_final.customer_code)),
                                                11)), check_two_line])
                if self.subtotal_amount_tax_child(0, record_final.customer_code):
                    a.append(['', '', '', '', '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.subtotal_amount_tax_child(0, record_final.customer_code)),
                                                11)), check_two_line])
                a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                          '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.amount_tax_child(10, record_final.customer_code)), 11)),
                          check_two_line])
                a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                          '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.amount_tax_child(8, record_final.customer_code)), 11)),
                          check_two_line])
                if self.amount_tax_child(0, record_final.customer_code):
                    a.append(['', '', '', '', '', '', '', '{0:,.0f}'.format(
                        self.limit_number_field(int(self.amount_tax_child(0, record_final.customer_code)), 11)),
                              check_two_line])
            a.append(['', '', '', '', '', '', '', '', 4])
            amount_tax_convert = '{0:,.0f}'.format(
                self.limit_number_field(int(record_final.bill_invoice_id.amount_tax), 11))
            amount_total_bill_convert = '{0:,.0f}'.format(self.limit_number_field(int(self.amount_total), 8))
            subtotal_amount_tax_10 = '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax(10)), 11))
            subtotal_amount_tax_8 = '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax(8)), 11))
            subtotal_amount_tax_0 = '{0:,.0f}'.format(self.limit_number_field(int(self.subtotal_amount_tax()), 11))
            # Check hang cuoi cung la invoice hay payment
            if record_final.bill_invoice_id:
                if record_final.x_voucher_tax_transfer == 'foreign_tax' or record_final.x_voucher_tax_transfer == 'voucher':
                    a.append(
                        ['', '', '消費税', '', '', '', '', amount_tax_convert, check_two_line])
                if record_final.bill_invoice_id.x_studio_summary:
                    a.append(['', '', '＜' + self.limit_charater_field(record_final.bill_invoice_id.x_studio_summary, 12) + '＞', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
                else:
                    a.append(['', '', '', '', '', '', '', '(' + str('{0:,.0f}'.format(self.limit_number_field(int(record_final.bill_invoice_id.amount_total), 8))) + ')', check_two_line])
            if self.partner_id.customer_tax_unit == 'invoice':
                a.append(['', '', '（税別御買上計）　　　　　（10％対象）', '',
                          '', '', '', subtotal_amount_tax_10, check_two_line])
                a.append(['', '', '　　　　　　　　　　　　　（8％対象）', '',
                          '', '', '', subtotal_amount_tax_8, check_two_line])
                if self.subtotal_amount_tax():
                    a.append(['', '', '', '', '', '', '', subtotal_amount_tax_0, check_two_line])
                if self.amount_tax(8):
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.tax_amount - self.amount_tax(8) - self.amount_tax()), 11)),
                              check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '',
                              '{0:,.0f}'.format(self.limit_number_field(
                                  int(self.amount_tax(8)), 11)), check_two_line])
                else:
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '',
                              '{0:,.0f}'.format(self.limit_number_field(int(self.tax_amount - self.amount_tax()), 11)),
                              check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax(8)), 11)),
                              check_two_line])
                if self.amount_tax():
                    a.append(['', '', '', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax()), 11)),
                              check_two_line])
            else:
                a.append(['', '', '【　合　　計　】', '', '', '', '', amount_total_bill_convert, check_two_line])
                a.append(['', '', '（税別御買上計）　　　　　（10％対象）', '',
                          '', '', '', subtotal_amount_tax_10, check_two_line])
                a.append(['', '', '　　　　　　　　　　　　　（8％対象）', '',
                          '', '', '', subtotal_amount_tax_8, check_two_line])
                if self.subtotal_amount_tax():
                    a.append(['', '', '', '', '', '', '', subtotal_amount_tax_0, check_two_line])
                if self.amount_tax(8):
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.tax_amount - self.amount_tax(8) - self.amount_tax()), 11)),
                              check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '',
                              '{0:,.0f}'.format(self.limit_number_field(
                                  int(self.amount_tax(8)), 11)), check_two_line])
                else:
                    a.append(['', '', '（消費税）　　　　　　　　（10％消費税）', '',
                              '', '', '',
                              '{0:,.0f}'.format(self.limit_number_field(int(self.tax_amount - self.amount_tax()), 11)),
                              check_two_line])
                    a.append(['', '', '　　　　　　　　　　　　　（8％消費税）', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax(8)), 11)),
                              check_two_line])
                if self.amount_tax():
                    a.append(['', '', '', '',
                              '', '', '', '{0:,.0f}'.format(self.limit_number_field(int(self.amount_tax()), 11)),
                              check_two_line])
        if a == []:
            a.append(['', '', '', '', '', '', '', '', 0])
        return a
    #TH - done

    # Limit Character and Number:
    def limit_charater_field(self, string_text=None, text_len=20, name=False, first1=True):
        text_len = text_len * 2
        count = 0
        len_string = ''
        COUNT_REPLACE = '〇'
        a = ' '
        if string_text:
            # string_text = jaconv.h2z(string_text, kana=True, digit=True, ascii=True).replace('\uff0d', '-').replace('\xa0', ' ').replace('\uff5e', '~')
            if name:
                string_text1 = ''
                string_text2 = ''
                if len(string_text.splitlines()) - 1:
                    string_text1 = string_text.splitlines()[0]
                    string_text2 = string_text.splitlines()[1]
                    string_text2_tmp = string_text2.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE).replace(' ', 'a')

                else:
                    string_text1 = string_text
                    string_text2 = ''
                    string_text1_tmp = string_text1.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE).replace(' ', 'a')
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
                    count = 0
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
            else:
                if not first1 and len(string_text.splitlines()) - 1:
                    for i in string_text.splitlines():
                        string_text += string_text.splitlines()[i]
                string_text_tmp = string_text.replace('\uff0d', COUNT_REPLACE).replace('\xa0', COUNT_REPLACE).replace('\uff5e', COUNT_REPLACE).replace(' ', 'a')
                count = 0
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


class PartnerClass(models.Model):
    _inherit = 'res.partner'

    def set_supplier_name(self):
        for i in self:
            if i.group_supplier:
                i.group_supplier = i.customer_supplier_group_code.name

    group_supplier = fields.Char('set_supplier_name', compute='set_supplier_name')


class InvoiceClassCustom(models.Model):
    _inherit = 'account.move'

    # account_invoice_id
    payment_id = fields.One2many('account.payment', 'account_invoice_id')
    bill_invoice_ids = fields.One2many('bill.invoice', 'account_move_id')
