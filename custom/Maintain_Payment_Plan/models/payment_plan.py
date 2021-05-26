from odoo import api, fields, models, tools
# from datetime import date
from datetime import date, timedelta
from odoo.tools.float_utils import float_round
import calendar
import datetime
dict_domain = {}

class PaymentPlan(models.Model):
    _name = 'payment.plan'
    _auto = False

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
    bill_invoice_ids = fields.One2many('bill.invoice', 'bill_info_id', string='Bill Invoice Ids')
    # report_status = fields.Char(string='Report Status', default='no report')
    hr_employee_id = fields.Many2one('hr.employee', string='Customer Agent')
    hr_department_id = fields.Many2one('hr.department', string='Department')
    business_partner_group_custom_id = fields.Many2one('business.partner.group.custom', string='Supplier Group')
    customer_closing_date_id = fields.Many2one('closing.date', string='Customer Closing Date')
    customer_excerpt_request = fields.Boolean(string='Excerpt Request', default=False)
    bill_report_state = fields.Boolean(string="Bill Report State", default=False)
    payment_cost_and_discount = fields.Float(string='Payment Cost And Discount')
    payment_plan_date = fields.Char(string='Payment Plan Date', store=True)

    # def _check_bill_in_month (listdata,record):
        # is_add_item = False
        # for item in listdata:
        #     if itm[1] == record.billing_code:
        #         closing_date_str1 = date.strftime(itm[3],'%Y') + date.strftime(itm[3],'%m')
        #         closing_date_str2 = record.closing_date.strftime('%Y') + record.closing_date.strftime('%m')
        #         if closing_date_str1 == closing_date_str2:
        #             if itm[3] < record.closing_date:
        #                 is_add_item = True
        #                 listdata.remove(itm)
        #
        #         else:
        #             is_add_item = True

        # return  is_add_item

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW payment_plan AS
            SELECT row_number() OVER(ORDER BY billing_code, payment_plan_date) AS id , * FROM(
                (SELECT
                    t1.partner_id,
                    t1.billing_code,
                    t1.billing_name,
                    t1.bill_no,
                    t1.bill_date,
                    t1.last_closing_date,
                    t1.closing_date,
                    t1.deadline,
                    t1.invoices_number,
                    t1.invoices_details_number,
                    t1.last_billed_amount_moved0,
                    t1.deposit_amount_moved0,
                    t1.balance_amount_moved0,
                    t1.amount_untaxed_moved0,
                    t1.tax_amount_moved0,
                    t1.amount_total_moved0,
                    t1.amount_untaxed_cashed_moved0,
                    t1.tax_amount_cashed_moved0,
                    t1.amount_total_cashed_moved0,
                    t1.billed_amount_moved0,
                    t1.active_flag,
                    t1.currency_id,
                    t1.hr_employee_id,
                    t1.hr_department_id,
                    t1.business_partner_group_custom_id,
                    t1.customer_closing_date_id,
                    t1.customer_excerpt_request,
                    t1.bill_report_state,
                    t1.create_uid,
                    t1.create_date,
                    t1.write_uid,
                    t1.write_date,
                    t1.search_x_studio_name,
                    t1.sale_rep_id,
                    t1.payment_cost_and_discount,
                    t1.payment_plan_date,
                    t1.payment_discount_in_invoicing_moved0,
                    t1.last_billed_amount_moved1,
                    t1.deposit_amount_moved1,
                    t1.balance_amount_moved1,
                    t1.amount_untaxed_moved1,
                    t1.tax_amount_moved1,
                    t1.amount_total_moved1,
                    t1.amount_untaxed_cashed_moved1,
                    t1.tax_amount_cashed_moved1,
                    t1.amount_total_cashed_moved1,
                    t1.billed_amount_moved1,
                    t1.payment_discount_in_invoicing_moved1,
                    t1.last_billed_amount,
                    t1.deposit_amount,
                    t1.balance_amount,
                    t1.amount_untaxed,
                    t1.tax_amount,
                    t1.amount_total,
                    t1.amount_untaxed_cashed,
                    t1.tax_amount_cashed,
                    t1.amount_total_cashed,
                    t1.billed_amount,
                    t1.payment_discount_in_invoicing
            FROM bill_info AS T1
            WHERE T1.closing_date = (SELECT MAX(T2.closing_date) FROM bill_info As T2 
						            WHERE T1.billing_code = T2.billing_code 
							        AND to_char(T1.closing_date,'YYYYMM')  = to_char(T2.closing_date,'YYYYMM')
						            GROUP BY T2.billing_code)
) ) AS foo""")

    def _compute_data(self):
        list_data_print = []
        list_data = []
        # record_draft = []
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)

        # last_seikyu_closing_date = date.min
        # self.sorted(key=lambda r: r.billing_code)

        for record in self:
            #Compute Employee Code
            record.employee_code = record.partner_id.customer_agent.employee_code

            #Compute Employee Name
            record.employee_name = record.partner_id.customer_agent.name

            #Compute Payment Date
            payment_date_day_cal = date.today().strftime('%d')
            payment_date_month_cal = date.today().strftime('%m')
            payment_date_year_cal = date.today().strftime('%Y')
            closing_date_year = record.closing_date.strftime('%Y')
            closing_date_month = record.closing_date.strftime('%m')
            closing_date_date = record.closing_date.strftime('%d')
            payment_date_month = record.partner_id.customer_payment_date.payment_month
            payment_date_date = record.partner_id.customer_payment_date.payment_date
            if payment_date_month == 'this_month':
                payment_date_day_cal = payment_date_date
                if int(closing_date_month) in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                    payment_date_day_cal = 30
                elif int(closing_date_month) == 2 and payment_date_day_cal >= 28:
                    payment_date_day_cal = 28
                if int(closing_date_date) < payment_date_day_cal:
                    payment_date_month_cal = int(closing_date_month)
                    payment_date_year_cal = int(closing_date_year)
                else:
                    if int(closing_date_month) == 12:
                        payment_date_month_cal = int(closing_date_month) - 11
                        payment_date_year_cal = int(closing_date_year) + 1
                    else:
                        payment_date_month_cal = int(closing_date_month) + 1
                        payment_date_year_cal = int(closing_date_year)
                        if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                            payment_date_day_cal = 30
                        elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                            payment_date_day_cal = 28
            elif payment_date_month == 'next_month':
                if int(closing_date_month) == 12:
                    payment_date_month_cal = int(closing_date_month) - 11
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 1
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'two_months_after':
                if int(closing_date_month) in (11, 12):
                    payment_date_month_cal = int(closing_date_month) - 10
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 2
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'three_months_after':
                if int(closing_date_month) in (10, 11, 12):
                    payment_date_month_cal = int(closing_date_month) - 9
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 3
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'four_months_after':
                if int(closing_date_month) in (9, 10, 11, 12):
                    payment_date_month_cal = int(closing_date_month) - 8
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 4
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'five_months_after':
                if int(closing_date_month) in (8, 9, 10, 11, 12):
                    payment_date_month_cal = int(closing_date_month) - 7
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 5
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'six_months_after':
                if int(closing_date_month) in (7, 8, 9, 10, 11, 12):
                    payment_date_month_cal = int(closing_date_month) - 6
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 6
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            payment_date_str = str(payment_date_month_cal) + '/' + str(payment_date_day_cal) + '/' + str(payment_date_year_cal)
            payment_date_obj = datetime.datetime.strptime(payment_date_str, '%m/%d/%Y').date()
            record.payment_plan_date = payment_date_obj
            record.payment_plan_date_display = payment_date_obj.strftime('%Y年%m月%d日')
            record.deposit_amount_count = 0
            record.payment_deposit_amount = 0
            # record_account_payment_amount_before_seikyu = 0

            #Compute Deposit Amount
            for record_account_payment in self.env['account.payment'].search([('partner_id', 'in', record.partner_id.ids)]):
                if (record.closing_date <= record_account_payment.payment_date) and (record_account_payment.payment_date < payment_date_obj):
                    record.payment_deposit_amount += record_account_payment.payment_amount

                # if (record_account_payment.payment_date >= last_seikyu_closing_date) and (record_account_payment.payment_date < record.closing_date) and (record_account_payment.payment_date < payment_date_obj):
                #     record_account_payment_amount_before_seikyu += record_account_payment.payment_amount

            # Compute Payment Amount Transfer
            # record.payment_amount_transfer = record.last_billed_amount

            # for i in record_draft:
            #     if record.billing_code == i[0]:
            #         record.payment_amount_transfer = i[1]
            #         record_draft.remove(i)
            # record.amount_untaxed_amount = record.amount_untaxed
            # record.tax_amount_amount = record.tax_amount
            #

            #Compute Billed Amount
            # record.payment_billed_amount = record.amount_untaxed_amount + record.tax_amount_amount + record.payment_amount_transfer - record_account_payment_amount_before_seikyu

            # Compute Must Payment Amount
            # record.payment_must_pay_amount = record.payment_billed_amount + record.payment_amount_transfer - record_account_payment_amount_before_seikyu
            # record.payment_must_pay_amount = record.payment_billed_amount

            record.payment_amount_transfer = record.balance_amount
            record.amount_untaxed_amount = record.amount_untaxed
            record.tax_amount_amount = record.tax_amount
            record.payment_billed_amount = record.billed_amount
            record.payment_must_pay_amount = record.billed_amount - record.payment_deposit_amount

            #Create List To Report
            is_add_item = True
            for item in list_data:
                if item[1] == record.billing_code:
                    closing_date_str1 = date.strftime(item[3], '%Y') + date.strftime(item[3], '%m')
                    closing_date_str2 = record.closing_date.strftime('%Y') + record.closing_date.strftime('%m')
                    if closing_date_str1 == closing_date_str2:
                        if item[3] < record.closing_date:  # Data closing date newer
                            list_data.remove(item)
                        else:
                            is_add_item = False             # Data closing date older
                    else:
                        is_add_item = True

            if is_add_item:
                list_data.append([record.payment_plan_date, record.billing_code, record.billing_name, record.closing_date, record.employee_code, record.employee_name,
                              record.payment_amount_transfer, record.amount_untaxed_amount, record.tax_amount_amount, record.payment_billed_amount, record.payment_deposit_amount, record.payment_must_pay_amount])
                # record_draft.append([record.billing_code, record.payment_must_pay_amount])
                # record_draft.append([record.billing_code, record.payment_billed_amount])
                list_data_print = [dict_domain[user.id], list_data]

            # last_seikyu_closing_date = record.closing_date

        return list_data_print

    employee_code = fields.Char(compute=_compute_data, store=False)
    employee_name = fields.Char(compute=_compute_data, store=False)
    payment_plan_date = fields.Char(compute=_compute_data, store=True)
    payment_plan_date_display = fields.Char(compute=_compute_data, store=False)
    payment_date_search = fields.Char(compute=_compute_data, store=False)
    payment_deposit_amount = fields.Integer(compute=_compute_data, store=False)
    payment_billed_amount = fields.Integer(compute=_compute_data, store=False)
    payment_must_pay_amount = fields.Integer(compute=_compute_data, store=False)
    payment_amount_transfer = fields.Integer(compute=_compute_data, store=False)
    amount_untaxed_amount = fields.Integer(compute=_compute_data, store=False)
    tax_amount_amount = fields.Integer(compute=_compute_data, store=False)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context.copy()
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        if ctx.get('have_advance_search'):
            domain = []
            if ctx.get('view_code') == 'payment_plan':
                domain = []
                dict_domain_in_search = {
                    'payment_date_name': '',
                    'payment_plan_date_gte': '',
                    'payment_plan_date_lte': '',
                    'closing_date_code': '',
                    'closing_date_gte': '',
                    'closing_date_lte': '',
                    'employee_code_gte': '',
                    'employee_code_lte': '',
                    'partner_group_code': '',
                    'billing_code_gte': '',
                    'billing_code_lte': '',
                }
                domain += [['partner_id.customer_payment_date.id', '!=', False]]
                for record in args:
                    if record[0] == '&':
                        continue
                    if record[0] == 'display_order':
                        if record[2] == '1':
                            order = 'payment_plan_date asc'
                        elif record[2] == '2':
                            order = 'hr_employee_id, payment_plan_date asc'
                        elif record[2] == '3':
                            order = 'closing_date asc'
                        elif record[2] == '4':
                            order = 'hr_employee_id, closing_date asc'
                    if record[0] != 'display_order':
                        domain += [record]
                    if record[0] == 'partner_id.customer_payment_date.name':
                        dict_domain_in_search['payment_date_name'] = record[2]
                    if record[0] == 'payment_plan_date' and record[1] == '>=':
                        dict_domain_in_search['payment_plan_date_gte'] = record[2]
                    if record[0] == 'payment_plan_date' and record[1] == '<=':
                        dict_domain_in_search['payment_plan_date_lte'] = record[2]
                    if record[0] == 'partner_id.customer_closing_date.closing_date_code':
                        dict_domain_in_search['closing_date_code'] = record[2]
                    if record[0] == 'closing_date' and record[1] == '>=':
                        dict_domain_in_search['closing_date_gte'] = record[2]
                    if record[0] == 'closing_date' and record[1] == '<=':
                        dict_domain_in_search['closing_date_lte'] = record[2]
                    if record[0] == 'partner_id.customer_agent.employee_code' and record[1] == '>=':
                        dict_domain_in_search['employee_code_gte'] = record[2]
                    if record[0] == 'partner_id.customer_agent.employee_code' and record[1] == '<=':
                        dict_domain_in_search['employee_code_lte'] = record[2]
                    if record[0] == 'business_partner_group_custom_id.partner_group_code':
                        dict_domain_in_search['partner_group_code'] = record[2]
                    if record[0] == 'billing_code' and record[1] == '>=':
                        dict_domain_in_search['billing_code_gte'] = record[2]
                    if record[0] == 'billing_code' and record[1] == '<=':
                        dict_domain_in_search['billing_code_lte'] = record[2]
                dict_domain[user.id] = dict_domain_in_search
                args = domain
        if ctx.get('view_code') == 'payment_plan' and len(args) == 0:
            return []

        return super(PaymentPlan, self).search(args, offset=offset, limit=limit, order=order, count=count)