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
    payment_plan_date = fields.Char(string='Payment Plan Date')

    payment_deposit_amount = fields.Integer(string='Deposit')
    payment_must_pay_amount = fields.Integer(string='Must Payment Amount')

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
--==============================================================================================
--==============================================================================================
            CREATE OR REPLACE FUNCTION public.next_month (
                    in_date DATE,
                    in_num_of_month int,
                    in_day int)
                
                RETURNS DATE
                
                LANGUAGE 'plpgsql'

            AS $BODY$
            
            DECLARE
                v_date date;
                v_last_day_of_month date;
                v_last_day int;
            
            BEGIN
                --=========================================
                -- Caculate next N-month
                --=========================================
                v_date := in_date + (in_num_of_month * '1 month'::INTERVAL);
                -- raise notice 'next_month() - Next Month - v_date := %', v_date;
            
                --=========================================
                -- Caculate last day of month
                --=========================================
                v_last_day_of_month := (DATE_TRUNC('month', v_date) + interval '1 month' - interval '1 day')::date;
                -- raise notice 'next_month() - Last day of month - v_last_day_of_month := %', v_last_day_of_month;
            
                v_last_day := EXTRACT(DAY FROM v_last_day_of_month)::int;
                -- raise notice 'next_month() - Last day (1) - v_last_day := %', v_last_day;
                -- raise notice 'next_month() - Last day (2) - in_day := %', in_day;
            
                IF in_day < v_last_day THEN
                    v_last_day := in_day;
                END IF;
                -- raise notice 'next_month() - Last day (3) - v_last_day := %', v_last_day;
            
                --=========================================
                -- Caculate Output Date
                --=========================================
                v_date := TO_DATE((TO_CHAR(v_date, 'YYYYMM') || v_last_day), 'YYYYMMDD');
            
                -- raise notice 'next_month() - Output Date - v_date := %', v_date;
                -- raise notice 'next_month() - Output Date - TO_CHAR(v_date, ''YYYY-MM-DD'') := %', TO_CHAR(v_date, 'YYYY-MM-DD');
            
                -- RETURN TO_CHAR(v_date, 'YYYY-MM-DD');
                RETURN v_date;
            
            END;
            $BODY$;

--==============================================================================================
--==============================================================================================
            CREATE OR REPLACE FUNCTION public.get_payment_plan_date (
            
                in_partner_id int,
                -- in_bill_no character varying,
                in_closing_date date
            
            )
            
                RETURNS DATE
            
                LANGUAGE 'plpgsql'
                --COST 100
                --VOLATILE PARALLEL UNSAFE
            AS $BODY$
            
            DECLARE
            
                -- v_closing_date date;
                v_payment_date date;
            
                -- v_customer_code character varying;
                -- v_customer_code_bill character varying;
                -- v_customer_name character varying;
            
                v_payment_day int;
                v_payment_month_int int;
                v_payment_month_char character varying;
            
            BEGIN
                --=========================================
                -- Get payment date from partner id
                --=========================================
                SELECT
                    -- customer.customer_code AS customer_code,
                    -- customer.customer_code_bill AS customer_code_bill,
                    -- customer.name AS customer_name,
            
                    payment_date.payment_date AS payment_day,
                    payment_date.payment_month AS payment_month
            
                -- INTO v_customer_code, v_customer_code_bill, v_customer_name, v_payment_day, v_payment_month_char;
                INTO v_payment_day, v_payment_month_char
            
                FROM
                    (SELECT
                        -- res_partner.customer_code AS customer_code,
                        -- res_partner.customer_code_bill AS customer_code_bill,
                        -- res_partner.name AS name,
            
                        res_partner.customer_payment_date AS customer_payment_date
            
                    FROM res_partner
                    WHERE res_partner.id = in_partner_id) AS customer
            
                    LEFT JOIN
                    
                    payment_date
                    
                    ON customer.customer_payment_date = payment_date.id;
                 
                -- raise notice 'get_payment_plan_date() - Partner ID      - in_partner_id := %', in_partner_id;
                -- raise notice 'get_payment_plan_date() - Customer Code   - v_customer_code := %', v_customer_code;
                -- raise notice 'get_payment_plan_date() - Billing Code    - v_customer_code_bill := %', v_customer_code_bill;
                -- raise notice 'get_payment_plan_date() - Customer Name   - v_customer_name := %', v_customer_name;
            
                -- raise notice 'get_payment_plan_date() - Payment Day (1) - v_payment_day := %', v_payment_day;
                
                --=========================================
                -- If Customer has no payment date
                --=========================================
                IF v_payment_day IS NULL THEN
            
                    v_payment_date := NULL;
                
                ELSE
                    --=========================================
                    -- Get closing date from bill no
                    --=========================================
                    -- SELECT bill_info.closing_date FROM bill_info WHERE bill_info.bill_no = in_bill_no
                    -- INTO v_closing_date;
            
                    -- raise notice 'get_payment_plan_date() - Bill No         - in_bill_no := %', in_bill_no;
                    -- raise notice 'get_payment_plan_date() - Closing Date    - v_closing_date := %', v_closing_date;
            
                    --=========================================
                    -- Caculate Payment Date
                    --=========================================
                    IF v_payment_day = 0 THEN
                        -- v_payment_day = TO_CHAR(v_closing_date, 'DD');
                        v_payment_day = TO_CHAR(in_closing_date, 'DD');
                    END IF;
            
                    -- raise notice 'get_payment_plan_date() - Payment Day (2) - v_payment_day := %', v_payment_day;
            
                    v_payment_month_int = (
                        CASE WHEN (v_payment_month_char = 'this_month') AND
                                (v_payment_day > CAST(TO_CHAR(in_closing_date, 'DD') AS INTEGER))
                                THEN 0 -- (after 0 month of closing_date) => number of next months = 0
            
                            WHEN (v_payment_month_char = 'this_month') AND
                                (v_payment_day <= CAST(TO_CHAR(in_closing_date, 'DD') AS INTEGER))
                                THEN 1 -- (after 1 month of closing_date) => number of next months = 1
                            
                            WHEN (v_payment_month_char = 'next_month') THEN 1 -- (after 1 month of closing_date) => number of next months = 1
                            WHEN (v_payment_month_char = 'two_months_after') THEN 2 -- (after 2 month of closing_date) => number of next months = 2
                            WHEN (v_payment_month_char = 'three_months_after') THEN 3 -- (after 3 month of closing_date) => number of next months = 3
                            WHEN (v_payment_month_char = 'four_months_after') THEN 4 -- (after 4 month of closing_date) => number of next months = 4
                            WHEN (v_payment_month_char = 'five_months_after') THEN 5 -- (after 5 month of closing_date) => number of next months = 5
                            WHEN (v_payment_month_char = 'six_months_after') THEN 6 -- (after 6 month of closing_date) => number of next months = 6
                            WHEN (v_payment_month_char = 'seven_months_after') THEN 7 -- (after 7 month of closing_date) => number of next months = 7
                            WHEN (v_payment_month_char = 'eight_months_after') THEN 8 -- (after 8 month of closing_date) => number of next months = 8
                            WHEN (v_payment_month_char = 'nine_months_after') THEN 9 -- (after 9 month of closing_date) => number of next months = 9
                            WHEN (v_payment_month_char = 'ten_months_after') THEN 10 -- (after 10 month of closing_date) => number of next months = 10
                            WHEN (v_payment_month_char = 'eleven_months_after') THEN 11 -- (after 11 month of closing_date) => number of next months = 11
                            ELSE 1
                        END
                    );
            
                    -- raise notice 'get_payment_plan_date() - Payment Month  - v_payment_month_char := %', v_payment_month_char;
                    -- raise notice 'get_payment_plan_date() - Payment Month  - v_payment_month_int := %', v_payment_month_int;
            
                    -- v_payment_date := next_month(v_closing_date, v_payment_month_int, v_payment_day);
                    v_payment_date := next_month(in_closing_date, v_payment_month_int, v_payment_day);
            
                END IF;
            
                -- raise notice 'get_payment_plan_date() - Payment Date  - v_payment_date := %', v_payment_date;
            
                RETURN v_payment_date;
            
            END;
            $BODY$;
--==============================================================================================
--==============================================================================================
            CREATE OR REPLACE VIEW payment_plan AS
            SELECT row_number() OVER(ORDER BY payment_plan_date asc, billing_code asc) AS id , * FROM(
                (SELECT
                    T1.balance_amount,
                    T1.amount_untaxed,
                    T1.tax_amount,
                    T1.billed_amount,
                    COALESCE(sum(account_payment.payment_amount), 0) AS payment_deposit_amount,
                    (T1.billed_amount - COALESCE(sum(account_payment.payment_amount), 0)) AS payment_must_pay_amount,
                    T1.partner_id,
                    T1.billing_code,
                    T1.billing_name,
                    T1.bill_no,
                    T1.bill_date,
                    T1.last_closing_date,
                    T1.closing_date,
                    get_payment_plan_date(T1.partner_id, T1.closing_date) AS payment_plan_date,
                    T1.deadline,
                    T1.invoices_number,
                    T1.invoices_details_number,
                    T1.active_flag,
                    T1.currency_id,
                    T1.hr_employee_id,
                    T1.hr_department_id,
                    T1.business_partner_group_custom_id,
                    T1.customer_closing_date_id,
                    T1.customer_excerpt_request,
                    T1.bill_report_state,
                    T1.create_uid,
                    T1.create_date,
                    T1.write_uid,
                    T1.write_date,
                    T1.search_x_studio_name,
                    T1.sale_rep_id,
                    T1.payment_cost_and_discount,
--                    T1.payment_plan_date,
                    T1.last_billed_amount,
                    T1.deposit_amount,
                    T1.amount_total,
                    T1.amount_untaxed_cashed,
                    T1.tax_amount_cashed,
                    T1.amount_total_cashed,
                    T1.payment_discount_in_invoicing
                FROM bill_info AS T1
                LEFT JOIN account_payment
                ON 
                    T1.partner_id = account_payment.partner_id
                    AND (account_payment.payment_date > T1.closing_date) 
                    AND (account_payment.payment_date <= get_payment_plan_date(T1.partner_id, T1.closing_date))
                WHERE T1.closing_date = 
                                 (SELECT MAX(T2.closing_date) FROM bill_info As T2 
                                 WHERE T1.billing_code = T2.billing_code 
                                 AND to_char(T1.closing_date,'YYYYMM')  = to_char(T2.closing_date,'YYYYMM')
                                 GROUP BY T2.billing_code)
                GROUP BY 
                    T1.partner_id,
                    T1.bill_no,
                    T1.closing_date,
                    T1.billing_code,
                    T1.billing_name,
                    T1.bill_date,
                    T1.last_closing_date,
                    T1.deadline,
                    T1.invoices_number,
                    T1.invoices_details_number,
                    T1.active_flag,
                    T1.currency_id,
                    T1.hr_employee_id,
                    T1.hr_department_id,
                    T1.business_partner_group_custom_id,
                    T1.customer_closing_date_id,
                    T1.customer_excerpt_request,
                    T1.bill_report_state,
                    T1.create_uid,
                    T1.create_date,
                    T1.write_uid,
                    T1.write_date,
                    T1.search_x_studio_name,
                    T1.sale_rep_id,
                    T1.payment_cost_and_discount,
                    T1.payment_plan_date,
                    T1.last_billed_amount,
                    T1.deposit_amount,
                    T1.balance_amount,
                    T1.amount_untaxed,
                    T1.tax_amount,
                    T1.amount_total,
                    T1.amount_untaxed_cashed,
                    T1.tax_amount_cashed,
                    T1.amount_total_cashed,
                    T1.billed_amount,
                    T1.payment_discount_in_invoicing
                )
            ) AS PP
            WHERE (PP.balance_amount <> 0)
                  OR (PP.amount_untaxed <> 0)
                  OR (PP.tax_amount <> 0)
                  OR (PP.billed_amount <> 0)
                  OR (PP.payment_deposit_amount <> 0)
                  OR (PP.payment_must_pay_amount <> 0);
""")

    def _compute_data(self):
        list_data_print = []
        list_data = []
        # record_draft = []
        # current_uid = self._context.get('uid')
        # user = self.env['res.users'].browse(current_uid)
        user = self.env.user

        # last_seikyu_closing_date = date.min
        # self.sorted(key=lambda r: r.billing_code)

        # for record in self:
            # # Compute Employee Code
            # record.employee_code = record.partner_id.customer_agent.employee_code
            #
            # # Compute Employee Name
            # record.employee_name = record.partner_id.customer_agent.name
            #
            # # Compute Payment Date
            # payment_date_day_cal = date.today().strftime('%d')
            # payment_date_month_cal = date.today().strftime('%m')
            # payment_date_year_cal = date.today().strftime('%Y')
            # closing_date_year = record.closing_date.strftime('%Y')
            # closing_date_month = record.closing_date.strftime('%m')
            # closing_date_date = record.closing_date.strftime('%d')
            # payment_date_month = record.partner_id.customer_payment_date.payment_month
            # payment_date_date = record.partner_id.customer_payment_date.payment_date
            # # Add 2021/07/09
            # if payment_date_date == 0:
            #     payment_date_date = int(closing_date_date)
            # # End 2021/07/09
            # if payment_date_month == 'this_month':
            #     payment_date_day_cal = payment_date_date
            #     if int(closing_date_month) in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #         payment_date_day_cal = 30
            #     elif int(closing_date_month) == 2 and payment_date_day_cal >= 28:
            #         payment_date_day_cal = 28
            #     if int(closing_date_date) < payment_date_day_cal:
            #         payment_date_month_cal = int(closing_date_month)
            #         payment_date_year_cal = int(closing_date_year)
            #     else:
            #         if int(closing_date_month) == 12:
            #             payment_date_month_cal = int(closing_date_month) - 11
            #             payment_date_year_cal = int(closing_date_year) + 1
            #         else:
            #             payment_date_month_cal = int(closing_date_month) + 1
            #             payment_date_year_cal = int(closing_date_year)
            #             if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #                 payment_date_day_cal = 30
            #             elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #                 payment_date_day_cal = 28
            # elif payment_date_month == 'next_month':
            #     if int(closing_date_month) == 12:
            #         payment_date_month_cal = int(closing_date_month) - 11
            #         payment_date_year_cal = int(closing_date_year) + 1
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            #     else:
            #         payment_date_month_cal = int(closing_date_month) + 1
            #         payment_date_year_cal = int(closing_date_year)
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            # elif payment_date_month == 'two_months_after':
            #     if int(closing_date_month) in (11, 12):
            #         payment_date_month_cal = int(closing_date_month) - 10
            #         payment_date_year_cal = int(closing_date_year) + 1
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            #     else:
            #         payment_date_month_cal = int(closing_date_month) + 2
            #         payment_date_year_cal = int(closing_date_year)
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            # elif payment_date_month == 'three_months_after':
            #     if int(closing_date_month) in (10, 11, 12):
            #         payment_date_month_cal = int(closing_date_month) - 9
            #         payment_date_year_cal = int(closing_date_year) + 1
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            #     else:
            #         payment_date_month_cal = int(closing_date_month) + 3
            #         payment_date_year_cal = int(closing_date_year)
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            # elif payment_date_month == 'four_months_after':
            #     if int(closing_date_month) in (9, 10, 11, 12):
            #         payment_date_month_cal = int(closing_date_month) - 8
            #         payment_date_year_cal = int(closing_date_year) + 1
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            #     else:
            #         payment_date_month_cal = int(closing_date_month) + 4
            #         payment_date_year_cal = int(closing_date_year)
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            # elif payment_date_month == 'five_months_after':
            #     if int(closing_date_month) in (8, 9, 10, 11, 12):
            #         payment_date_month_cal = int(closing_date_month) - 7
            #         payment_date_year_cal = int(closing_date_year) + 1
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            #     else:
            #         payment_date_month_cal = int(closing_date_month) + 5
            #         payment_date_year_cal = int(closing_date_year)
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            # elif payment_date_month == 'six_months_after':
            #     if int(closing_date_month) in (7, 8, 9, 10, 11, 12):
            #         payment_date_month_cal = int(closing_date_month) - 6
            #         payment_date_year_cal = int(closing_date_year) + 1
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            #     else:
            #         payment_date_month_cal = int(closing_date_month) + 6
            #         payment_date_year_cal = int(closing_date_year)
            #         payment_date_day_cal = payment_date_date
            #         if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
            #             payment_date_day_cal = 30
            #         elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
            #             payment_date_day_cal = 28
            # payment_date_str = str(payment_date_month_cal) + '/' + str(payment_date_day_cal) + '/' + str(payment_date_year_cal)
            # payment_date_obj = datetime.datetime.strptime(payment_date_str, '%m/%d/%Y').date()
            # record.payment_plan_date = payment_date_obj
            # record.payment_plan_date_display = payment_date_obj.strftime('%Y年%m月%d日')
            # record.deposit_amount_count = 0
            # record.payment_deposit_amount = 0
            # # record_account_payment_amount_before_seikyu = 0
            #
            # # Compute Deposit Amount
            # for record_account_payment in self.env['account.payment'].search([('partner_id', 'in', record.partner_id.ids)]):
            #     if (record.closing_date <= record_account_payment.payment_date) and (record_account_payment.payment_date < payment_date_obj):
            #         record.payment_deposit_amount += record_account_payment.payment_amount
            #
            #     # if (record_account_payment.payment_date >= last_seikyu_closing_date) and (record_account_payment.payment_date < record.closing_date) and (record_account_payment.payment_date < payment_date_obj):
            #     #     record_account_payment_amount_before_seikyu += record_account_payment.payment_amount
            #
            # # Compute Payment Amount Transfer
            # # record.payment_amount_transfer = record.last_billed_amount
            #
            # # for i in record_draft:
            # #     if record.billing_code == i[0]:
            # #         record.payment_amount_transfer = i[1]
            # #         record_draft.remove(i)
            # # record.amount_untaxed_amount = record.amount_untaxed
            # # record.tax_amount_amount = record.tax_amount
            # #
            #
            # # Compute Billed Amount
            # # record.payment_billed_amount = record.amount_untaxed_amount + record.tax_amount_amount + record.payment_amount_transfer - record_account_payment_amount_before_seikyu
            #
            # # Compute Must Payment Amount
            # # record.payment_must_pay_amount = record.payment_billed_amount + record.payment_amount_transfer - record_account_payment_amount_before_seikyu
            # # record.payment_must_pay_amount = record.payment_billed_amount

        for record in self:

            # Compute Employee Code
            record.employee_code = record.partner_id.customer_agent.employee_code

            # Compute Employee Name
            record.employee_name = record.partner_id.customer_agent.name

            # Compute Payment Date
            record.payment_plan_date_display = ''
            if record.payment_plan_date:
                record.payment_plan_date_display = record.payment_plan_date.strftime('%Y年%m月%d日')

            record.payment_amount_transfer = record.balance_amount
            record.amount_untaxed_amount = record.amount_untaxed
            record.tax_amount_amount = record.tax_amount
            record.payment_billed_amount = record.billed_amount
            # record.payment_must_pay_amount = record.billed_amount - record.payment_deposit_amount
            record.payment_deposit_amount = record.payment_deposit_amount
            # record.payment_must_pay_amount = record.payment_must_pay_amount

            # # Create List To Report
            # is_add_item = True
            # for item in list_data:
            #     if item[1] == record.billing_code:
            #         closing_date_str1 = date.strftime(item[3], '%Y') + date.strftime(item[3], '%m')
            #         closing_date_str2 = record.closing_date.strftime('%Y') + record.closing_date.strftime('%m')
            #         if closing_date_str1 == closing_date_str2:
            #             if item[3] < record.closing_date:  # Data closing date newer
            #                 list_data.remove(item)
            #             else:
            #                 is_add_item = False  # Data closing date older
            #         else:
            #             is_add_item = True
            #
            # if is_add_item:
            list_data.append([record.payment_plan_date, record.billing_code, record.billing_name, record.closing_date, record.employee_code, record.employee_name,
                              record.payment_amount_transfer, record.amount_untaxed_amount, record.tax_amount_amount, record.payment_billed_amount, record.payment_deposit_amount,
                              record.payment_must_pay_amount])
            # record_draft.append([record.billing_code, record.payment_must_pay_amount])
            # record_draft.append([record.billing_code, record.payment_billed_amount])
            list_data_print = [dict_domain[user.id], list_data]

            # last_seikyu_closing_date = record.closing_date

        return list_data_print

    employee_code = fields.Char(compute=_compute_data, store=False)
    employee_name = fields.Char(compute=_compute_data, store=False)
    # payment_plan_date = fields.Char(compute=_compute_data, store=False)
    payment_plan_date_display = fields.Char(compute=_compute_data, store=False)
    # payment_date_search = fields.Char(compute=_compute_data, store=False)

    payment_amount_transfer = fields.Integer(compute=_compute_data, store=False)
    amount_untaxed_amount = fields.Integer(compute=_compute_data, store=False)
    tax_amount_amount = fields.Integer(compute=_compute_data, store=False)
    payment_billed_amount = fields.Integer(compute=_compute_data, store=False)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context.copy()
        # current_uid = self._context.get('uid')
        # user = self.env['res.users'].browse(current_uid)
        user = self.env.user

        if ctx.get('have_advance_search'):
            domain = []
            billing_ids = []
            billing_query = []
            employee_ids = []
            employee_query = []
            if ctx.get('view_code') == 'payment_plan':
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
                # domain += [['partner_id.customer_payment_date.id', '!=', False]]
                for arg in args:
                    if arg[0] == '&':
                        continue
                    elif arg[0] == 'display_order':
                        if arg[2] == '1':
                            order = 'payment_plan_date asc'
                        elif arg[2] == '2':
                            order = 'hr_employee_id, payment_plan_date asc'
                        elif arg[2] == '3':
                            order = 'closing_date asc'
                        elif arg[2] == '4':
                            order = 'hr_employee_id, closing_date asc'
                        continue
                    elif arg[0] == 'partner_id.customer_payment_date.name':
                        dict_domain_in_search['payment_date_name'] = arg[2]
                    elif arg[0] == 'payment_plan_date' and arg[1] == '>=':
                        dict_domain_in_search['payment_plan_date_gte'] = arg[2]
                    elif arg[0] == 'payment_plan_date' and arg[1] == '<=':
                        dict_domain_in_search['payment_plan_date_lte'] = arg[2]
                    elif arg[0] == 'partner_id.customer_closing_date.closing_date_code':
                        dict_domain_in_search['closing_date_code'] = arg[2]
                    elif arg[0] == 'closing_date' and arg[1] == '>=':
                        dict_domain_in_search['closing_date_gte'] = arg[2]
                    elif arg[0] == 'closing_date' and arg[1] == '<=':
                        dict_domain_in_search['closing_date_lte'] = arg[2]
                    elif arg[0] == 'partner_id.customer_agent.employee_code':
                        if arg[1] == '>=':
                            dict_domain_in_search['employee_code_gte'] = arg[2]
                        elif arg[1] == '<=':
                            dict_domain_in_search['employee_code_lte'] = arg[2]
                        employee_query.append("LOWER(employee_code) {0} '{1}'".format(arg[1], arg[2].lower()))
                        continue
                    elif arg[0] == 'business_partner_group_custom_id.partner_group_code':
                        dict_domain_in_search['partner_group_code'] = arg[2]
                    elif arg[0] == 'billing_code':
                        if arg[1] == '>=':
                            dict_domain_in_search['billing_code_gte'] = arg[2]
                        elif arg[1] == '<=':
                            dict_domain_in_search['billing_code_lte'] = arg[2]
                        billing_query.append("LOWER(billing_code) {0} '{1}'".format(arg[1], arg[2].lower()))
                        continue
                    domain += [arg]
            if billing_query:
                query = 'SELECT id FROM payment_plan WHERE ' + ' AND '.join(billing_query)
                self._cr.execute(query)
                query_res = self._cr.dictfetchall()
                for employee_record in query_res:
                    billing_ids.append(employee_record.get('id'))
                domain += [['id', 'in', billing_ids]]
            if employee_query:
                query = 'SELECT id FROM hr_employee WHERE ' + ' AND '.join(employee_query)
                self._cr.execute(query)
                query_res = self._cr.dictfetchall()
                for employee_record in query_res:
                    employee_ids.append(employee_record.get('id'))
                domain += [['partner_id.customer_agent', 'in', employee_ids]]
            dict_domain[user.id] = dict_domain_in_search
            args = domain
        if ctx.get('view_code') == 'payment_plan' and len(args) == 0:
            return []

        return super(PaymentPlan, self).search(args, offset=offset, limit=limit, order=order, count=count)
