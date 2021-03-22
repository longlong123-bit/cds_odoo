from odoo import api, fields, models, tools
from datetime import datetime, date
import datetime

dict_domain_customer = {}

class SalesAchievementCustomer(models.Model):
    _name = 'sales.achievement.customer'
    _auto = False

    hr_employee_employee_code = fields.Char(string='Employee Code', readonly=True)
    hr_employee_name = fields.Char(string='Employee Name', readonly=True)
    res_partner_customer_code = fields.Char(string='Customer Code', readonly=True)
    res_partner_name = fields.Char(string='Customer Name', readonly=True)
    sum_pay_amount_final = fields.Float(string='Sum Pay Amount', readonly=True)
    sum_return_amount_final = fields.Float(string='Sum Return Amount', readonly=True)
    sum_discount_amount_final = fields.Float(string='Sum Discount Amount', readonly=True)
    net_sale_amount_final = fields.Float(string='Net Sale Amount', readonly=True)
    gross_amount_final = fields.Float(string='Gross Amount', readonly=True)

    def init(self, check_date = '', check_date_gte_or_lte = '', date_gte = datetime.datetime.now().strftime('%Y/%m/%d'), date_lte = datetime.datetime.now().strftime('%Y/%m/%d')):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
        CREATE OR REPLACE VIEW sales_achievement_customer AS

        SELECT row_number() OVER(ORDER BY hr_employee_employee_code) AS id , *  FROM(
            (SELECT hr_employee_employee_code,
	            hr_employee_name,
                res_partner_customer_code,
                res_partner_name,
                SUM(CASE WHEN 'nodate'= %s THEN sum_pay_amount WHEN 'date_gte' = %s AND date >= %s THEN sum_pay_amount WHEN 'date_lte' = %s AND date <= %s THEN sum_pay_amount
                WHEN date between %s and %s THEN sum_pay_amount ELSE 0 END) AS sum_pay_amount_final,
	            SUM(CASE WHEN 'nodate'= %s THEN sum_return_amount WHEN 'date_gte' = %s AND date >= %s THEN sum_return_amount WHEN 'date_lte' = %s AND date <= %s THEN sum_return_amount
	            WHEN date between %s and %s THEN sum_return_amount ELSE 0 END) AS sum_return_amount_final,
	            SUM(CASE WHEN 'nodate'= %s THEN sum_discount_amount WHEN 'date_gte' = %s AND date >= %s THEN sum_discount_amount WHEN 'date_lte' = %s AND date <= %s THEN sum_discount_amount
	            WHEN date between %s and %s THEN sum_discount_amount ELSE 0 END) AS sum_discount_amount_final,
	            SUM(CASE WHEN 'nodate'= %s THEN sum_cost_price WHEN 'date_gte' = %s AND date >= %s THEN sum_cost_price WHEN 'date_lte' = %s AND date <= %s THEN sum_cost_price
	            WHEN date between %s and %s THEN sum_cost_price ELSE 0 END) AS sum_cost_price_final,
	            SUM(CASE WHEN 'nodate'= %s THEN net_sale_amount WHEN 'date_gte' = %s AND date >= %s THEN net_sale_amount WHEN 'date_lte' = %s AND date <= %s THEN net_sale_amount
	            WHEN date between %s and %s THEN net_sale_amount ELSE 0 END) AS net_sale_amount_final,
	            SUM(CASE WHEN 'nodate'= %s THEN gross_amount WHEN 'date_gte' = %s AND date >= %s THEN gross_amount WHEN 'date_lte' = %s AND date <= %s THEN gross_amount
	            WHEN date between %s and %s THEN gross_amount ELSE 0 END) AS gross_amount_final
            FROM
	            (SELECT account_move_line.date,
		            account_move_line.partner_id,
		            res_employee.hr_employee_name,
	                pay_amount.sum_pay_amount,
			 	    return_amount.sum_return_amount,
	                discount_amount.sum_discount_amount,
	 			    cost_price.sum_cost_price,
			 	    coalesce(sum_pay_amount, 0) + coalesce(sum_return_amount, 0) + coalesce(sum_discount_amount, 0) AS net_sale_amount,
			 	    coalesce(sum_pay_amount, 0) + coalesce(sum_return_amount, 0) + coalesce(sum_discount_amount, 0) - coalesce(cost_price.sum_cost_price, 0) AS gross_amount ,
	                res_employee.hr_employee_employee_code,
	                res_employee.res_partner_name,
			 	    res_employee.res_partner_customer_code
                FROM
                    account_move_line
                        LEFT JOIN
                            (SELECT hr_employee.employee_code AS hr_employee_employee_code,
				                hr_employee.name AS hr_employee_name,
				                res_partner.id AS join_partner_id,
				                res_partner.name AS res_partner_name,
						        res_partner.customer_code AS res_partner_customer_code
		                    FROM res_partner
		                        LEFT JOIN hr_employee
		                        ON res_partner.customer_agent = hr_employee.id
		                    ) AS res_employee
                        ON account_move_line.partner_id = res_employee.join_partner_id
	 			        LEFT JOIN
				            (SELECT date AS pay_amount_date,
					            partner_id AS pay_amount_partner_id,
					            x_invoicelinetype AS pay_amount_x_invoicelinetype,
					            SUM(account_move_line.price_total) AS sum_pay_amount
					        FROM account_move_line
					        WHERE x_invoicelinetype = '通常'
					            AND account_move_line.parent_state = 'posted'
					            AND account_move_line.account_internal_type != 'receivable'
					        GROUP BY account_move_line.date, account_move_line.partner_id,
					            account_move_line.x_invoicelinetype
				            ) AS pay_amount
	 			        ON pay_amount.pay_amount_date = account_move_line.date and pay_amount.pay_amount_partner_id = account_move_line.partner_id
                        LEFT JOIN
				            (SELECT date AS return_amount_date,
					            partner_id AS return_amount_partner_id,
					            x_invoicelinetype AS return_amount_x_invoicelinetype,
					            SUM(account_move_line.price_total) AS sum_return_amount
					        FROM account_move_line WHERE x_invoicelinetype = '返品'
					            AND account_move_line.parent_state = 'posted'
					            AND account_move_line.account_internal_type != 'receivable'
					        GROUP BY account_move_line.date, account_move_line.partner_id,  account_move_line.x_invoicelinetype
				            ) AS return_amount
	 			        ON return_amount.return_amount_date = account_move_line.date and return_amount.return_amount_partner_id = account_move_line.partner_id
	 			        LEFT JOIN
				            (SELECT date AS discount_amount_date,
					            partner_id AS discount_amount_partner_id,
					            x_invoicelinetype AS discount_amount_x_invoicelinetype,
					            SUM(account_move_line.price_total) AS sum_discount_amount
					        FROM account_move_line WHERE x_invoicelinetype = '値引'
					            AND account_move_line.parent_state = 'posted'
					            AND account_move_line.account_internal_type != 'receivable'
					        GROUP BY account_move_line.date, account_move_line.partner_id,  account_move_line.x_invoicelinetype
				            ) AS discount_amount
	 			        ON discount_amount.discount_amount_date = account_move_line.date and discount_amount.discount_amount_partner_id = account_move_line.partner_id
	 			        LEFT JOIN
	 			            (SELECT date AS cost_price_date,
					            partner_id AS cost_price_partner_id,
					            x_invoicelinetype AS cost_price_x_invoicelinetype,
					            SUM(account_move_line.x_product_cost_price) AS sum_cost_price
					        FROM account_move_line WHERE
					            account_move_line.parent_state = 'posted'
					        AND account_move_line.account_internal_type != 'receivable'
					        GROUP BY account_move_line.date, account_move_line.partner_id,  account_move_line.x_invoicelinetype
				            ) AS cost_price
	 			        ON account_move_line.date = cost_price.cost_price_date AND account_move_line.partner_id = cost_price.cost_price_partner_id
                WHERE account_move_line.parent_state = 'posted'
	 		        AND account_move_line.account_internal_type != 'receivable'
			        AND (pay_amount.pay_amount_x_invoicelinetype = account_move_line.x_invoicelinetype
				        OR return_amount.return_amount_x_invoicelinetype = account_move_line.x_invoicelinetype
				        OR discount_amount.discount_amount_x_invoicelinetype = account_move_line.x_invoicelinetype)
	 	        GROUP BY account_move_line.date,
			        account_move_line.partner_id,
			        res_employee.res_partner_name,
			        pay_amount.sum_pay_amount,
			        return_amount.sum_return_amount,
			        discount_amount.sum_discount_amount,
			        res_employee.hr_employee_employee_code,
			        res_employee.hr_employee_name,
			        res_employee.res_partner_customer_code,
			        net_sale_amount,
			        account_move_line.x_product_cost_price,
	 		        cost_price.sum_cost_price
		        ORDER BY date, partner_id
    	        ) AS customer_final
            GROUP BY hr_employee_employee_code,
	            hr_employee_name,
                res_partner_customer_code,
                res_partner_name
            )
        ) AS foo""", [check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte])

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
            Overriding function search from file models.py
            File path Override: /odoo/models.py
        """
        domain = self._get_condition_search_of_module(self=self, args=args)
        res = self._search(args=domain, offset=offset, limit=limit, order=order, count=count)
        return res if count else self.browse(res)

    @staticmethod
    def _get_condition_search_of_module(self, args):
        domain = []
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        timenow = datetime.datetime.now().strftime('%Y/%m/%d')
        args_init = {'date_gte': '',
                     'date_lte': ''}
        sales_achievement_customer_context = self._context.copy()
        if sales_achievement_customer_context and 'sales_achievement_customer' in sales_achievement_customer_context:
            dict_domain_in_search = {
                'hr_employee_name_gte': '',
                'hr_employee_name_lte': '',
                'hr_employee_employee_code_gte': '',
                'hr_employee_employee_code_lte': '',
                'res_partner_customer_code_gte': '',
                'res_partner_customer_code_lte': ''
            }
            for record in args:
                if record[0] == '&':
                    continue
                if record[0] == 'hr_employee_name' and record[1] == '>=':
                    args_init['date_gte'] = record[2]
                    dict_domain_in_search['hr_employee_name_gte'] = record[2]
                    continue
                if record[0] == 'hr_employee_name' and record[1] == '<=':
                    args_init['date_lte'] = record[2]
                    dict_domain_in_search['hr_employee_name_lte'] = record[2]
                    continue
                if record[0] != 'hr_employee_name':
                    domain += [record]
                if record[0] == 'hr_employee_employee_code' and record[1] == '>=':
                    dict_domain_in_search['hr_employee_employee_code_gte'] = record[2]
                if record[0] == 'hr_employee_employee_code' and record[1] == '<=':
                    dict_domain_in_search['hr_employee_employee_code_lte'] = record[2]
                if record[0] == 'res_partner_customer_code' and record[1] == '>=':
                    dict_domain_in_search['res_partner_customer_code_gte'] = record[2]
                if record[0] == 'res_partner_customer_code' and record[1] == '<=':
                    dict_domain_in_search['res_partner_customer_code_lte'] = record[2]
            dict_domain_customer[user.id] = dict_domain_in_search

            if args_init['date_gte'] and args_init['date_lte']:
                self.init('date', 'date', args_init['date_gte'], args_init['date_lte'])
            elif args_init['date_gte'] and args_init['date_lte'] == '':
                self.init('date', 'date_gte', args_init['date_gte'], timenow)
            elif args_init['date_lte'] and args_init['date_gte'] == '':
                self.init('date', 'date_lte', timenow, args_init['date_lte'])
            else:
                self.init('nodate', 'date', timenow, timenow)
            args = domain
        return args

    def passConditionInSearchToReport(self):
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        list_domain = [dict_domain_customer[user.id]]
        return list_domain