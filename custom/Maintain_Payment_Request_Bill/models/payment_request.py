from odoo import api, fields, models
# from datetime import date
from datetime import date, timedelta
from odoo.tools.float_utils import float_round
from . import payment_request_bill
import calendar
import jaconv


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

    def count_detail_line(self):
        self.ensure_one()
        count_detail = 1
        count = len(self.product_name.splitlines()) - 1
        if self.tax_rate == 8 or self.account_move_line_id.product_id.product_tax_category == 'exempt':
            count_detail += 1
        if count > 0:
            count_detail += 1
        return count_detail

    def gross_maker_and_standard(self):
        self.ensure_one()
        gross = ''
        if self.product_maker_name and self.product_custom_standardnumber:
            gross = str(self.product_maker_name) + ' ' + str(self.product_custom_standardnumber)
        elif self.product_maker_name and not self.product_custom_standardnumber:
            gross = str(self.product_maker_name)
        else:
            gross = self.product_custom_standardnumber
        if gross:
            gross = jaconv.h2z(gross, kana=True, digit=True, ascii=True)[:10]
        return gross


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
        for line in self.bill_detail_ids:
            if line.x_voucher_tax_transfer and (
                    line.tax_rate == tax_rate or (tax_rate == 0 and line.tax_rate != 10 and line.tax_rate != 8)):
                subtotal += line.line_amount
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
            if tax_rate == 0 and line.x_voucher_tax_transfer == 'custom_tax':
                subtotal += re.amount_tax
        return rounding(subtotal, 0, self.partner_id.customer_tax_rounding)

    def subtotal_amount_tax_child(self, tax_rate=0, customer_code=None):
        subtotal = 0
        for line in self.bill_detail_ids:
            if line.customer_code == customer_code:
                if line.x_voucher_tax_transfer and (
                        line.tax_rate == tax_rate or (tax_rate == 0 and line.tax_rate != 10 and line.tax_rate != 8)):
                    subtotal += line.line_amount
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
        print(count_line)
        return count_line

    # Limit Character and Number:
    def limit_charater_field(self, string_text=None, text_len=20, name=False, first1=True):
        len_string = ''
        if string_text:
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
                        string_text += string_text.splitlines()[i]
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
