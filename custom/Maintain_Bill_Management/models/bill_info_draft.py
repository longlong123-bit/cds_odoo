from odoo import models, fields, api


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
                            if len(string_text1_tmp[count].encode(
                                    'shift_jisx0213')) > 1 and byte_count < text_len - 1:
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
                            if len(string_text2_tmp[count].encode(
                                    'shift_jisx0213')) > 1 and byte_count < text_len - 1:
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
                string_text_tmp = string_text.replace('\uff0d', COUNT_REPLACE).replace('\xa0',
                                                                                       COUNT_REPLACE).replace(
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

    _sql_constraints = [('bill_info_draft', 'unique(billing_code, last_closing_date, deadline)', 'This data has been billed.')]


