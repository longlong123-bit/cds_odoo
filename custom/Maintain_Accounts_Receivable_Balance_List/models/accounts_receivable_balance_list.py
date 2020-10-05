# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, date, timedelta
import calendar, pytz

# initialize global variable
# 対象月
val_target_month = ''
# 事業部
val_division = ''
# 営業担当者
val_sales_rep = ''
# 取引先グループ
val_customer_supplier_group_code = ''
# 請求先
val_customer_code_bill_from = ''
val_customer_code_bill_to = ''
# 表示順
val_display_order = ''

# global variable for bill
val_bill_search_deadline = ''


class AccountsReceivableBalanceList(models.Model):
    _inherit = 'res.partner'

    # billing liabilities flag
    billing_liabilities_flg = fields.Boolean('Billing Liabilities Flag', default=False)

    # list fields
    # 前月売掛残
    accounts_receivable_last_month = fields.Integer('Accounts Receivable Last Month', compute='_compute_liabilities',
                                                    default='0', store=False)
    # 入金額
    deposit_amount = fields.Integer('Deposit Amount', compute='_compute_liabilities', default='0', store=False)
    # 繰越金額
    amount_carried_forward = fields.Integer('Amount Carried Forward', compute='_compute_liabilities',
                                            default='0', store=False)
    # 御買上金額
    purchase_amount = fields.Integer('Purchase Amount', compute='_compute_liabilities', default='1000', store=False)
    # 消費税
    consumption_tax = fields.Integer('Consumption Tax', compute='_compute_liabilities', default='500', store=False)
    # 値引額
    discount = fields.Integer('Discount', default='0', store=False)
    # 今月売掛残高
    liabilities = fields.Integer(string='Accounts Receivable Balance This Month', compute='_compute_liabilities',
                                 default='0', store=False)

    # fields input condition advanced search
    input_target_month = fields.Char('Input Target Date', compute='_compute_liabilities', default='', store=False)
    input_division = fields.Char('Input Division', compute='_compute_liabilities', default='', store=False)
    input_sales_rep = fields.Char('Input Sales Representative', compute='_compute_liabilities', default='', store=False)
    input_customer_supplier_group_code = fields.Char('Input Customer Supplier Group Code',
                                                     compute='_compute_liabilities', default='', store=False)
    input_customer_code_bill_from = fields.Char('Input Customer Code Bill From', compute='_compute_liabilities',
                                                default='',
                                                store=False)
    input_customer_code_bill_to = fields.Char('Input Customer Code Bill To', compute='_compute_liabilities', default='',
                                              store=False)
    input_display_order = fields.Char('Input Display Order', compute='_compute_liabilities', default='', store=False)

    def init(self):
        """
            Init of module
        """
        # update data billing_liabilities_flg when install or upgrade module
        self._cr.execute("""
            UPDATE res_partner
                SET billing_liabilities_flg = 't'
                WHERE customer_code = customer_code_bill;
            UPDATE res_partner
                SET billing_liabilities_flg = 'f'
                WHERE customer_code != customer_code_bill
                    OR customer_code IS NULL
                    OR customer_code_bill IS NULL;
        """)

    @api.constrains('id')
    def _compute_liabilities(self):
        """
            Compute Accounts Receivable Balance In The Month Selected
        """
        # set domain for 'division' and 'sales_rep'
        domain = []
        if val_division:
            domain += [('department_id', '=', int(val_division))]
        if val_sales_rep:
            domain += [('id', '=', int(val_sales_rep))]
        # get information table hr_employee from domain
        hr_employee_ids = []
        if domain:
            hr_employee_ids = self.env["hr.employee"].search(domain)
        # get array user_id from hr_employee_ids
        user_id = []
        for row in hr_employee_ids:
            if row.user_id.id:
                user_id.append(row.user_id.id)

        # get closing date
        closing_date = self._compute_closing_date(year_month_selected=val_target_month)

        condition_division_sales_rep = domain and (user_id and ' AND x_userinput_id in (%s)' % (
            ','.join(str(e) for e in user_id)) or ' AND x_userinput_id is null') or ' '
        info_liabilities = self._get_info_liabilities(condition_division_sales_rep=condition_division_sales_rep,
                                                      closing_date=closing_date)

        # set information Accounts receivable balance list
        for item in self:
            item.accounts_receivable_last_month = 0
            item.deposit_amount = 0
            item.amount_carried_forward = 0
            item.purchase_amount = 0
            item.consumption_tax = 0
            item.liabilities = 0
            if info_liabilities:
                for item_info_liabilities in info_liabilities:
                    if item.id == item_info_liabilities[0]:
                        deposits = self.env['account.payment'].search(
                            [('partner_id', '=', item.id),
                             ('payment_date', '>=', closing_date['last_closing_date']),
                             ('payment_date', '<=', closing_date['current_closing_date']),
                             ('state', '=', 'draft')])
                        amount_total_signed_last_month = item_info_liabilities[1] and item_info_liabilities[1] or 0
                        deposit_amount_last_month = item_info_liabilities[2] and item_info_liabilities[2] or 0
                        # deposit_amount = item_info_liabilities[3] and item_info_liabilities[3] or 0
                        deposit_amount = sum(deposits.mapped('amount'))
                        purchase_amount = item_info_liabilities[4] and item_info_liabilities[4] or 0
                        consumption_tax = item_info_liabilities[5] and item_info_liabilities[5] or 0

                        accounts_receivable_last_month = amount_total_signed_last_month - deposit_amount_last_month
                        amount_carried_forward = accounts_receivable_last_month - deposit_amount

                        item.accounts_receivable_last_month = accounts_receivable_last_month
                        item.deposit_amount = deposit_amount
                        item.amount_carried_forward = amount_carried_forward
                        item.purchase_amount = purchase_amount
                        item.consumption_tax = consumption_tax
                        item.liabilities = amount_carried_forward + purchase_amount + consumption_tax

            # set the value to use for the program report
            item.input_target_month = datetime.strptime(val_target_month, '%Y-%m').strftime('%Y年%m月')
            item.input_division = val_division
            item.input_sales_rep = val_sales_rep
            item.input_customer_supplier_group_code = val_customer_supplier_group_code
            item.input_customer_code_bill_from = val_customer_code_bill_from
            item.input_customer_code_bill_to = val_customer_code_bill_to
            item.input_display_order = val_display_order

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
            Overriding function search from file models.py
            File path Override: /odoo/models.py
        """
        # ctx = self._context.copy()
        module_context = self._context.copy()
        if module_context and module_context.get('liabilities_module'):
            get_condition_search_of_module = self._get_condition_search_of_module(self=self, args=args)
            args = get_condition_search_of_module['args']
            if get_condition_search_of_module['order']:
                order = get_condition_search_of_module['order']
        else:
            if module_context.get('have_advance_search'):
                domain = []
                check = 0
                arr = ["department", "customer_code", "customer_code_bill", "name", "customer_name_kana",
                       "street", "customer_phone", "customer_state", "customer_supplier_group_code",
                       "customer_industry_code", "customer_agent"]
                for record in args:
                    if record[0] == '&':
                        continue
                    if record[0] == 'search_category' and record[2] == 'equal':
                        check = 1
                    if check == 1 and record[0] in arr:
                        record[1] = '=ilike'
                    if record[0] == 'name':
                        domain += ['|', ['customer_name_2', record[1], record[2]]]
                    if 'customer_closing_date' == record[0]:
                        if record[2].isnumeric():
                            record[0] = 'customer_closing_date.start_day'
                            record[1] = '='
                    if 'customer_except_request' == record[0]:
                        if record[2] == 'True':
                            record[2] = True
                        elif record[2] == 'False':
                            record[2] = False
                        else:
                            continue
                    if 'deadline' == record[0]:
                        global val_bill_search_deadline
                        val_bill_search_deadline = record[2]
                    if record[0] != 'search_category':
                        domain += [record]
                args = domain
        if 'Billing' == module_context.get('view_name') and len(args) == 1:
            return []
        # res = super(AccountsReceivableBalanceList, self).search(args=domain, offset=offset, limit=limit, order=order, count=count)
        return super(AccountsReceivableBalanceList, self).search(args, offset=offset, limit=limit, order=order,
                                                                 count=count)

    @api.constrains('customer_code', 'customer_code_bill')
    def _check_billing_liabilities(self):
        """
            Update field 'billing_liabilities_Flg' in table res_partner
            When fields 'customer_code' and 'customer_code_bill' change
        """
        for record in self:
            # Customer has customer_code equal with customer_code_bill
            if record.customer_code == record.customer_code_bill:
                record.billing_liabilities_Flg = True
            else:
                record.billing_liabilities_Flg = False

    def _compute_closing_date(self, year_month_selected):
        """
            Compute closing date of company
        """
        # get information closing date
        company_closing_date = self._get_company_closing_date()
        _start = 1
        if company_closing_date:
            _start = company_closing_date

        if year_month_selected:
            # set date when input condition
            selected_date = datetime.strptime(year_month_selected, '%Y-%m').date()
        else:
            # set current date
            selected_date = datetime.now().astimezone(pytz.timezone(self.env.user.tz))

        # get closing date of year_month_selected
        if _start >= 28:
            # get days in month
            days_in_month = calendar.monthrange(selected_date.year, selected_date.month)[1]
            # set current closing date
            _current_closing_date = selected_date.replace(day=days_in_month)

            if selected_date.month == 1:
                # set last closing date
                _last_closing_date = selected_date.replace(year=selected_date.year - 1, month=12, day=31)
            else:
                # get days previous month
                days_previous_month = calendar.monthrange(selected_date.year, selected_date.month - 1)[1]
                # set last closing date
                _last_closing_date = selected_date.replace(month=selected_date.month - 1, day=days_previous_month)
        else:
            # set current closing date
            _current_closing_date = selected_date.replace(day=_start)

            if selected_date.month == 1:
                # set last closing date
                _last_closing_date = selected_date.replace(year=selected_date.year - 1, month=12, day=_start)
            else:
                # set last closing date
                _last_closing_date = selected_date.replace(month=selected_date.month - 1, day=_start)

        closing_date = {
            'last_closing_date': _last_closing_date,
            'current_closing_date': _current_closing_date,
        }

        return closing_date

    def _get_company_closing_date(self):
        """
            Get closing date from res_company
        """
        # get closing date from res_company
        company_closing_date = self.env['res.users'].search([['id', '=', self.env.uid]]).company_id.company_closing_date
        # return day closing
        return company_closing_date

    def _get_info_liabilities(self, condition_division_sales_rep, closing_date):
        """
            Get information about liabilities
        """
        query = "SELECT " \
                "   DISTINCT commercial_partner_id, " \
                "   SUM(amount_total) FILTER (WHERE x_studio_date_invoiced <= '{last_closing_date}') " \
                "       over(PARTITION BY commercial_partner_id) AS amount_total_signed_last_month, " \
                "   (SELECT SUM(payment_amount) AS sum_payment_amount " \
                "       FROM account_payment " \
                "       WHERE " \
                "           account_payment.partner_id = account_move.commercial_partner_id " \
                "           AND payment_date <= '{last_closing_date}' " \
                "       GROUP BY account_payment.partner_id " \
                "   ) AS deposit_amount_last_month," \
                "   (SELECT SUM(payment_amount) AS sum_payment_amount " \
                "       FROM account_payment " \
                "       WHERE " \
                "           account_payment.partner_id = account_move.commercial_partner_id " \
                "           AND payment_date BETWEEN '{last_closing_date}' AND '{current_closing_date}' " \
                "       GROUP BY account_payment.partner_id " \
                "   ) AS deposit_amount," \
                "   SUM(amount_untaxed) FILTER (WHERE x_studio_date_invoiced BETWEEN " \
                "       '{last_closing_date}' AND '{current_closing_date}') " \
                "       over(PARTITION BY commercial_partner_id) AS purchase_amount, " \
                "   SUM(amount_tax) FILTER (WHERE x_studio_date_invoiced BETWEEN " \
                "       '{last_closing_date}' AND '{current_closing_date}') " \
                "       over(PARTITION BY commercial_partner_id) AS consumption_tax " \
                "FROM account_move " \
                "WHERE state='posted' " \
                "   {condition_division_sales_rep} " \
                "GROUP BY " \
                "   commercial_partner_id, " \
                "   amount_total, " \
                "   x_studio_date_invoiced, " \
                "   amount_tax," \
                "   amount_untaxed".format(
            last_closing_date=closing_date['last_closing_date'],
            current_closing_date=closing_date['current_closing_date'],
            condition_division_sales_rep=condition_division_sales_rep
        )

        self._cr.execute(query)
        return self._cr.fetchall()

    @staticmethod
    def _get_condition_search_of_module(self, args):
        """
            Get condition search of module
        """
        domain = []
        # using global keyword
        global val_target_month
        global val_division
        global val_sales_rep
        global val_customer_supplier_group_code
        global val_customer_code_bill_from
        global val_customer_code_bill_to
        global val_display_order
        # reset global keyword
        val_target_month = datetime.now().astimezone(pytz.timezone(self.env.user.tz)).strftime('%Y-%m')
        val_division = ''
        val_sales_rep = ''
        val_customer_supplier_group_code = ''
        val_customer_code_bill_from = ''
        val_customer_code_bill_to = ''
        val_display_order = '担当者請求先（コード）'
        order = 'user_id'

        for record in args:
            if record[0] == '&':
                continue
            if record[0] == 'target_month':
                val_target_month = record[2]
                continue
            if record[0] == 'division':
                val_division = record[2]
                continue
            if record[0] == 'sales_rep':
                val_sales_rep = record[2]
                continue
            if record[0] == 'customer_supplier_group_code':
                val_customer_supplier_group_code = int(record[2])
                record[2] = int(record[2])
            if record[0] == 'customer_code_bill_from':
                val_customer_code_bill_from = record[2]
                record[0] = 'customer_code_bill'
            if record[0] == 'customer_code_bill_to':
                val_customer_code_bill_to = record[2]
                record[0] = 'customer_code_bill'
            if record[0] == 'display_order':
                if record[2] == '1':
                    order = 'customer_code_bill'
                    val_display_order = '請求先（コード）'
                continue
            domain += [record]

        result = {
            'args': domain,
            'order': order
        }

        return result
