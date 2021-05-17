from odoo import api, fields, models
# from datetime import date
from datetime import date, timedelta
from odoo.tools.float_utils import float_round
import calendar
import datetime
dict_domain = {}

class PaymentPlan(models.Model):
    _inherit = 'bill.info'

    def _compute_data(self):
        list_data_print = []
        list_data = []
        record_draft = []
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        last_seikyu_closing_date = date.min

        self.sorted(key=lambda r: (r.billing_code, r.closing_date))

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
            record_account_payment_amount_before_seikyu = 0
            record_account_payment_amount_after_seikyu = 0

            #Compute Deposit Amount
            for record_account_payment in self.env['account.payment'].search([('partner_id', 'in', record.partner_id.ids)]):
                if (record.closing_date <= record_account_payment.payment_date) and (record_account_payment.payment_date < payment_date_obj):
                    record_account_payment_amount_after_seikyu += record_account_payment.payment_amount
                    record.payment_deposit_amount = record_account_payment_amount_after_seikyu

                if (record_account_payment.payment_date >= last_seikyu_closing_date) and (record_account_payment.payment_date < record.closing_date) and (record_account_payment.payment_date < payment_date_obj):
                    record_account_payment_amount_before_seikyu += record_account_payment.payment_amount

            # Compute Payment Amount Transfer
            for i in record_draft:
                if record.billing_code == i[0]:
                    record.payment_amount_transfer = i[1]
                    record_draft.remove(i)
            record.amount_untaxed_amount = record.amount_untaxed
            record.tax_amount_amount = record.tax_amount
            #Compute Billed Amount
            record.payment_billed_amount = record.amount_untaxed_amount + record.tax_amount_amount + record.payment_amount_transfer - record_account_payment_amount_before_seikyu

            # Compute Must Payment Amount
            # record.payment_must_pay_amount = record.payment_billed_amount + record.payment_amount_transfer - record_account_payment_amount_before_seikyu
            record.payment_must_pay_amount = record.payment_billed_amount - record.payment_deposit_amount
            # record.payment_must_pay_amount = record.payment_billed_amount

            #Create List To Report
            list_data.append([record.payment_plan_date, record.billing_code, record.billing_name, record.closing_date, record.employee_code, record.employee_name,
                          record.payment_amount_transfer, record.amount_untaxed_amount, record.tax_amount_amount, record.payment_billed_amount, record.payment_deposit_amount, record.payment_must_pay_amount])
            # record_draft.append([record.billing_code, record.payment_must_pay_amount])
            record_draft.append([record.billing_code, record.payment_billed_amount])
            list_data_print = [dict_domain[user.id], list_data]

            last_seikyu_closing_date = record.closing_date

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



