from odoo import models, fields, api
from odoo.tools.float_utils import float_round

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

class BillInfoClass(models.Model):
    _name = 'bill.info.draft'

    partner_id = fields.Many2one('res.partner')

    billing_code = fields.Char(string='Billing Code')
    billing_name = fields.Char(string='Billing Name')
    bill_no = fields.Char(string='Bill No')
    bill_date = fields.Date(string='Bill Date')
    last_closing_date = fields.Date(string='Last Closing Date')
    closing_date = fields.Date(string='Closing Date')
    deadline = fields.Date(string='Deadline')
    invoices_number = fields.Integer(string='Number of Invoices', default=0)
    invoices_details_number = fields.Integer(string='Number of Invoice Details', default=0)
    last_billed_amount = fields.Monetary(string='Last Billed Amount', currency_field='currency_id')
    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id')
    balance_amount = fields.Monetary(string='Balance Amount', currency_field='currency_id')
    amount_untaxed = fields.Monetary(string='Amount Untaxed', currency_field='currency_id')
    tax_amount = fields.Monetary(string='Tax Amount', currency_field='currency_id')
    amount_total = fields.Monetary(string="Amount Total", currency_field='currency_id')
    amount_untaxed_cashed = fields.Monetary(string='Amount Untaxed Cashed', currency_field='currency_id')
    tax_amount_cashed = fields.Monetary(string='Tax Amount Cashed', currency_field='currency_id')
    amount_total_cashed = fields.Monetary(string="Amount Total Cashed", currency_field='currency_id')
    billed_amount = fields.Monetary(string='Billed Amount', currency_field='currency_id')
    payment_discount_in_invoicing = fields.Monetary(currency_field='currency_id')
    active_flag = fields.Boolean(default=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    bill_invoice_ids = fields.One2many('bill.invoice.draft', 'bill_info_id', string='Bill Invoice Ids')
    # report_status = fields.Char(string='Report Status', default='no report')
    hr_employee_id = fields.Many2one('hr.employee', string='Customer Agent')
    hr_department_id = fields.Many2one('hr.department', string='Department')
    business_partner_group_custom_id = fields.Many2one('business.partner.group.custom', string='Supplier Group')
    customer_closing_date_id = fields.Many2one('closing.date', string='Customer Closing Date')
    customer_excerpt_request = fields.Boolean(string='Excerpt Request', default=False)
    bill_report_state = fields.Boolean(string="Bill Report State", default=False)
    payment_cost_and_discount = fields.Float(string='Payment Cost And Discount')
    payment_plan_date = fields.Char(string='Payment Plan Date', store=True)

    last_billed_amount_int_format = fields.Integer(string='Last Billed Amount', compute='_last_billed_amount_int_format'
                                                   , readonly=True)
    deposit_amount_int_format = fields.Integer(string='Deposit Amount', compute='_deposit_amount_int_format'
                                               , readonly=True)
    balance_amount_int_format = fields.Integer(string='Balance Amount', compute='_balance_amount_int_format'
                                               , readonly=True)

    amount_untaxed_int_format = fields.Integer(string='Amount Untaxed', compute='_amount_untaxed_int_format'
                                               , readonly=True)

    tax_amount_int_format = fields.Integer(string='Tax Amount', compute='_tax_amount_int_format', readonly=True)

    amount_total_int_format = fields.Integer(string="Amount Total", compute='_amount_total_int_format', readonly=True)

    billed_amount_int_format = fields.Integer(string='Billed Amount', compute='_billed_amount_int_format'
                                              , readonly=True)

    def _last_billed_amount_int_format(self):
        for rec in self:
            rec.last_billed_amount_int_format = int(rec.last_billed_amount)

    def _deposit_amount_int_format(self):
        for rec in self:
            rec.deposit_amount_int_format = int(rec.deposit_amount)

    def _balance_amount_int_format(self):
        for rec in self:
            rec.balance_amount_int_format = int(rec.balance_amount)

    def _amount_untaxed_int_format(self):
        for rec in self:
            rec.amount_untaxed_int_format = int(rec.amount_untaxed)

    def _tax_amount_int_format(self):
        for rec in self:
            rec.tax_amount_int_format = int(rec.tax_amount)

    def _amount_total_int_format(self):
        for rec in self:
            rec.amount_total_int_format = int(rec.amount_total)

    def _billed_amount_int_format(self):
        for rec in self:
            rec.billed_amount_int_format = int(rec.billed_amount)

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
            if tax_rate == 0 and line.x_voucher_tax_transfer == 'custom_tax':
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



