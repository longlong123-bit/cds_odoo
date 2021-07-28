from odoo import api, fields, models, tools
from datetime import datetime, date
import datetime

from odoo.http import request

# dict_domain_business = {}


class SalesAchievementBusiness(models.Model):
    _name = 'sales.achievement.business'
    _auto = False

    business_partner_code = fields.Char(string='Business Partner Code', readonly=True)
    business_partner_name = fields.Char(string='Business Partner Name', readonly=True)

    # sum_pay_amount_final = fields.Integer(string='Sum Pay Amount', readonly=True,
    #                                     compute='_get_sum_pay_amount_final')
    sum_pay_amount_final = fields.Float(string='Sum Pay Amount', readonly=True,
                                        compute='_get_sum_pay_amount_final')
    sum_return_amount_final = fields.Float(string='Sum Return Amount', readonly=True,
                                           compute='_get_sum_return_amount_final')
    sum_discount_amount_final = fields.Float(string='Sum Discount Amount', readonly=True,
                                             compute='_get_sum_discount_amount_final')
    sum_cost_price_amount_final = fields.Float(string='Sum Cost Price Amount', readonly=True,
                                               compute='_get_sum_cost_price_amount_final')
    net_sale_amount_final = fields.Float(string='Net Sale Amount', readonly=True,
                                         compute='_get_net_sale_amount_final')
    gross_amount_final = fields.Float(string='Gross Amount', readonly=True,
                                      compute='_get_gross_amount_final')

    sum_pay_amount_final_no_tax = fields.Float(string='Sum Pay Amount', readonly=True)
    sum_return_amount_final_no_tax = fields.Float(string='Sum Return Amount', readonly=True)
    sum_discount_amount_final_no_tax = fields.Float(string='Sum Discount Amount', readonly=True)
    sum_cost_price_amount_final_no_tax = fields.Float(string='Sum Cost Price Amount', readonly=True)
    net_sale_amount_final_no_tax = fields.Float(string='Net Sale Amount', readonly=True)
    gross_amount_final_no_tax = fields.Float(string='Gross Amount', readonly=True)

    sum_pay_amount_final_include_tax = fields.Float(string='Sum Pay Amount', readonly=True)
    sum_return_amount_final_include_tax = fields.Float(string='Sum Return Amount', readonly=True)
    sum_discount_amount_final_include_tax = fields.Float(string='Sum Discount Amount', readonly=True)
    sum_cost_price_amount_final_include_tax = fields.Float(string='Sum Cost Price Amount', readonly=True)
    net_sale_amount_final_include_tax = fields.Float(string='Net Sale Amount', readonly=True)
    gross_amount_final_include_tax = fields.Float(string='Gross Amount', readonly=True)

    def _get_sum_pay_amount_final(self):
        for rec in self:
            if request.session['advanced_search_condition_of_business'][self.env.uid]['tax_class'] == '税込':
                # rec.sum_pay_amount_final = round(rec.sum_pay_amount_final_include_tax)
                rec.sum_pay_amount_final = rec.sum_pay_amount_final_include_tax
            else:
                rec.sum_pay_amount_final = rec.sum_pay_amount_final_no_tax

    def _get_sum_return_amount_final(self):
        for rec in self:
            if request.session['advanced_search_condition_of_business'][self.env.uid]['tax_class'] == '税込':
                rec.sum_return_amount_final = rec.sum_return_amount_final_include_tax
            else:
                rec.sum_return_amount_final = rec.sum_return_amount_final_no_tax

    def _get_sum_discount_amount_final(self):
        for rec in self:
            if request.session['advanced_search_condition_of_business'][self.env.uid]['tax_class'] == '税込':
                rec.sum_discount_amount_final = rec.sum_discount_amount_final_include_tax
            else:
                rec.sum_discount_amount_final = rec.sum_discount_amount_final_no_tax

    def _get_sum_cost_price_amount_final(self):
        for rec in self:
            if request.session['advanced_search_condition_of_business'][self.env.uid]['tax_class'] == '税込':
                rec.sum_cost_price_amount_final = rec.sum_cost_price_amount_final_include_tax
            else:
                rec.sum_cost_price_amount_final = rec.sum_cost_price_amount_final_no_tax

    def _get_net_sale_amount_final(self):
        for rec in self:
            if request.session['advanced_search_condition_of_business'][self.env.uid]['tax_class'] == '税込':
                rec.net_sale_amount_final = rec.net_sale_amount_final_include_tax
            else:
                rec.net_sale_amount_final = rec.net_sale_amount_final_no_tax

    def _get_gross_amount_final(self):
        for rec in self:
            if request.session['advanced_search_condition_of_business'][self.env.uid]['tax_class'] == '税込':
                rec.gross_amount_final = rec.gross_amount_final_include_tax
            else:
                rec.gross_amount_final = rec.gross_amount_final_no_tax

    def init(self, check_date = '', check_date_gte_or_lte = '', date_gte = datetime.datetime.now().strftime('%Y/%m/%d'), date_lte = datetime.datetime.now().strftime('%Y/%m/%d')):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
        CREATE OR REPLACE VIEW sales_achievement_business AS

        SELECT row_number() OVER(ORDER BY business_partner_code) AS id , *  FROM(
            (SELECT business_partner_code,
                business_partner_name,

                SUM(CASE WHEN 'nodate'= %s THEN sum_pay_amount WHEN 'date_gte' = %s AND date >= %s THEN sum_pay_amount WHEN 'date_lte' = %s AND date <= %s THEN sum_pay_amount
                WHEN date between %s and %s THEN sum_pay_amount ELSE 0 END) AS sum_pay_amount_final_no_tax,

                SUM(CASE WHEN 'nodate'= %s THEN sum_pay_amount_include_tax WHEN 'date_gte' = %s AND date >= %s THEN sum_pay_amount_include_tax WHEN 'date_lte' = %s AND date <= %s THEN sum_pay_amount_include_tax
                WHEN date between %s and %s THEN sum_pay_amount_include_tax ELSE 0 END) AS sum_pay_amount_final_include_tax,

                
                SUM(CASE WHEN 'nodate'= %s THEN sum_return_amount WHEN 'date_gte' = %s AND date >= %s THEN sum_return_amount WHEN 'date_lte' = %s AND date <= %s THEN sum_return_amount
                WHEN date between %s and %s THEN sum_return_amount ELSE 0 END) AS sum_return_amount_final_no_tax,

                SUM(CASE WHEN 'nodate'= %s THEN sum_return_amount_include_tax WHEN 'date_gte' = %s AND date >= %s THEN sum_return_amount_include_tax WHEN 'date_lte' = %s AND date <= %s THEN sum_return_amount_include_tax
                WHEN date between %s and %s THEN sum_return_amount_include_tax ELSE 0 END) AS sum_return_amount_final_include_tax,

                
                SUM(CASE WHEN 'nodate'= %s THEN sum_discount_amount WHEN 'date_gte' = %s AND date >= %s THEN sum_discount_amount WHEN 'date_lte' = %s AND date <= %s THEN sum_discount_amount
                WHEN date between %s and %s THEN sum_discount_amount ELSE 0 END) AS sum_discount_amount_final_no_tax,

                SUM(CASE WHEN 'nodate'= %s THEN sum_discount_amount_include_tax WHEN 'date_gte' = %s AND date >= %s THEN sum_discount_amount_include_tax WHEN 'date_lte' = %s AND date <= %s THEN sum_discount_amount_include_tax
                WHEN date between %s and %s THEN sum_discount_amount_include_tax ELSE 0 END) AS sum_discount_amount_final_include_tax,

                
                SUM(CASE WHEN 'nodate'= %s THEN sum_cost_price WHEN 'date_gte' = %s AND date >= %s THEN sum_cost_price WHEN 'date_lte' = %s AND date <= %s THEN sum_cost_price
                WHEN date between %s and %s THEN sum_cost_price ELSE 0 END) AS sum_cost_price_amount_final_no_tax,

                SUM(CASE WHEN 'nodate'= %s THEN sum_cost_price_include_tax WHEN 'date_gte' = %s AND date >= %s THEN sum_cost_price_include_tax WHEN 'date_lte' = %s AND date <= %s THEN sum_cost_price_include_tax
                WHEN date between %s and %s THEN sum_cost_price_include_tax ELSE 0 END) AS sum_cost_price_amount_final_include_tax,

                
                SUM(CASE WHEN 'nodate'= %s THEN net_sale_amount WHEN 'date_gte' = %s AND date >= %s THEN net_sale_amount WHEN 'date_lte' = %s AND date <= %s THEN net_sale_amount
                WHEN date between %s and %s THEN net_sale_amount ELSE 0 END) AS net_sale_amount_final_no_tax,

                SUM(CASE WHEN 'nodate'= %s THEN net_sale_amount_include_tax WHEN 'date_gte' = %s AND date >= %s THEN net_sale_amount_include_tax WHEN 'date_lte' = %s AND date <= %s THEN net_sale_amount_include_tax
                WHEN date between %s and %s THEN net_sale_amount_include_tax ELSE 0 END) AS net_sale_amount_final_include_tax,

                
                SUM(CASE WHEN 'nodate'= %s THEN gross_amount WHEN 'date_gte' = %s AND date >= %s THEN gross_amount WHEN 'date_lte' = %s AND date <= %s THEN gross_amount
                WHEN date between %s and %s THEN gross_amount ELSE 0 END) AS gross_amount_final_no_tax,

                SUM(CASE WHEN 'nodate'= %s THEN gross_amount_include_tax WHEN 'date_gte' = %s AND date >= %s THEN gross_amount_include_tax WHEN 'date_lte' = %s AND date <= %s THEN gross_amount_include_tax
                WHEN date between %s and %s THEN gross_amount_include_tax ELSE 0 END) AS gross_amount_final_include_tax

            FROM
--                (SELECT date,
--                    business_partner_code,
--                    business_partner_name,
--
--                    SUM(sum_pay_amount) AS sum_pay_amount,
--                    SUM(sum_pay_amount_include_tax) AS sum_pay_amount_include_tax,
--
--                    SUM(sum_return_amount) AS sum_return_amount,
--                    SUM(sum_return_amount_include_tax) AS sum_return_amount_include_tax,
--
--                    SUM(sum_discount_amount) AS sum_discount_amount,
--                    SUM(sum_discount_amount_include_tax) AS sum_discount_amount_include_tax,
--
--                    SUM(sum_cost_price) AS sum_cost_price,
--                    SUM(sum_cost_price_include_tax) AS sum_cost_price_include_tax,
--
--                    SUM(net_sale_amount) AS net_sale_amount,
--                    SUM(net_sale_amount_include_tax) AS net_sale_amount_include_tax,
--
--                    SUM(gross_amount) AS gross_amount,
--                    SUM(gross_amount_include_tax) AS gross_amount_include_tax
--                FROM
                    (SELECT account_move_line.date,
                        account_move_line.partner_id,
                        res_business_partner.business_partner_code,

                        pay_amount.sum_pay_amount,
                        pay_amount.sum_pay_amount_include_tax,

                        return_amount.sum_return_amount,
                        return_amount.sum_return_amount_include_tax,

                        discount_amount.sum_discount_amount,
                        discount_amount.sum_discount_amount_include_tax,

                        cost_price.sum_cost_price,
                        cost_price.sum_cost_price_include_tax,

                        coalesce(sum_pay_amount, 0) + coalesce(sum_return_amount, 0) + coalesce(sum_discount_amount, 0) AS net_sale_amount,
                        coalesce(sum_pay_amount_include_tax, 0) + coalesce(sum_return_amount_include_tax, 0) + coalesce(sum_discount_amount_include_tax, 0) AS net_sale_amount_include_tax,

                        coalesce(sum_pay_amount, 0) + coalesce(sum_return_amount, 0) + coalesce(sum_discount_amount, 0) - coalesce(cost_price.sum_cost_price, 0) AS gross_amount ,
                        --coalesce(sum_pay_amount_include_tax, 0) + coalesce(sum_return_amount_include_tax, 0) + coalesce(sum_discount_amount_include_tax, 0) - coalesce(cost_price.sum_cost_price_include_tax, 0) AS gross_amount_include_tax ,
                        coalesce(sum_pay_amount, 0) + coalesce(sum_return_amount, 0) + coalesce(sum_discount_amount, 0) - coalesce(cost_price.sum_cost_price, 0) AS gross_amount_include_tax ,

                        res_business_partner.business_partner_name,
                        res_business_partner.res_partner_name,
                        res_business_partner.res_partner_customer_code
                    FROM
                        account_move_line
                            LEFT JOIN
                                (SELECT business_partner_group_custom.partner_group_code AS business_partner_code,
                                        business_partner_group_custom.name AS business_partner_name,
                                        res_partner.id AS join_partner_id,
                                        res_partner.name AS res_partner_name,
                                        res_partner.customer_code AS res_partner_customer_code
                                FROM res_partner
                                    LEFT JOIN
                                        business_partner_group_custom
                                    ON res_partner.customer_supplier_group_code = business_partner_group_custom.id
                                ) AS res_business_partner
                            ON account_move_line.partner_id = res_business_partner.join_partner_id

                            LEFT JOIN
                                (SELECT date AS pay_amount_date,
                                    partner_id AS pay_amount_partner_id,
                                    x_invoicelinetype AS pay_amount_x_invoicelinetype,

                                    SUM(account_move_line.quantity * account_move_line.price_no_tax) AS sum_pay_amount,
                                    SUM(account_move_line.quantity * account_move_line.price_include_tax) AS sum_pay_amount_include_tax
                                
                                FROM account_move_line
                                WHERE x_invoicelinetype = '通常'
                                    AND account_move_line.parent_state = 'posted'
                                    AND account_move_line.account_internal_type != 'receivable'
                                GROUP BY account_move_line.date, account_move_line.partner_id,  account_move_line.x_invoicelinetype
                                ) AS pay_amount
                            ON pay_amount.pay_amount_date = account_move_line.date and pay_amount.pay_amount_partner_id = account_move_line.partner_id

                            LEFT JOIN
                                (SELECT date AS return_amount_date,
                                    partner_id AS return_amount_partner_id,
                                    x_invoicelinetype AS return_amount_x_invoicelinetype,

                                    SUM(account_move_line.quantity * account_move_line.price_no_tax) AS sum_return_amount,
                                    SUM(account_move_line.quantity * account_move_line.price_include_tax) AS sum_return_amount_include_tax
                                
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

                                    SUM(account_move_line.quantity * account_move_line.price_no_tax) AS sum_discount_amount,
                                    SUM(account_move_line.quantity * account_move_line.price_include_tax) AS sum_discount_amount_include_tax

                                FROM account_move_line WHERE x_invoicelinetype = '値引'
                                    AND account_move_line.parent_state = 'posted'
                                    AND account_move_line.account_internal_type != 'receivable'
                                GROUP BY account_move_line.date, account_move_line.partner_id,  account_move_line.x_invoicelinetype
                                ) AS discount_amount
                            ON discount_amount.discount_amount_date = account_move_line.date and discount_amount.discount_amount_partner_id = account_move_line.partner_id

                            LEFT JOIN
                                (SELECT date AS cost_price_date,
                                    partner_id AS cost_price_partner_id,
                                    -- x_invoicelinetype AS cost_price_x_invoicelinetype, 

                                    ABS(SUM(account_move_line.quantity * account_move_line.x_product_cost_price)) AS sum_cost_price,
                                    -- ABS(SUM(account_move_line.x_product_cost_price * (1 + (account_move_line.tax_rate / 100)))) AS sum_cost_price_include_tax
                                    ABS(SUM(account_move_line.quantity * account_move_line.x_product_cost_price)) AS sum_cost_price_include_tax

                                FROM account_move_line
                                WHERE account_move_line.parent_state = 'posted'
                                    AND account_move_line.account_internal_type != 'receivable'
                                GROUP BY account_move_line.date, account_move_line.partner_id
                                --,  account_move_line.x_invoicelinetype
                                ) AS cost_price
                            ON account_move_line.date = cost_price.cost_price_date AND account_move_line.partner_id = cost_price.cost_price_partner_id

                    WHERE account_move_line.parent_state = 'posted'
                        AND account_move_line.account_internal_type != 'receivable'
                        AND (pay_amount.pay_amount_x_invoicelinetype = account_move_line.x_invoicelinetype
                            OR return_amount.return_amount_x_invoicelinetype = account_move_line.x_invoicelinetype
                            OR discount_amount.discount_amount_x_invoicelinetype = account_move_line.x_invoicelinetype)
    
                    GROUP BY account_move_line.date,
                        account_move_line.partner_id,
                        res_business_partner.res_partner_name,
    
                        res_business_partner.business_partner_code,
                        res_business_partner.business_partner_name,
                        res_business_partner.res_partner_customer_code,
    
                        pay_amount.sum_pay_amount,
                        pay_amount.sum_pay_amount_include_tax,
    
                        return_amount.sum_return_amount,
                        return_amount.sum_return_amount_include_tax,
    
                        discount_amount.sum_discount_amount,
                        discount_amount.sum_discount_amount_include_tax,
    
                        --account_move_line.x_product_cost_price,
                        cost_price.sum_cost_price,
                        cost_price.sum_cost_price_include_tax
    
                        --net_sale_amount,
                        --net_sale_amount_include_tax,
    
                        -- gross_amount,
                        -- gross_amount_include_tax
    
                    ORDER BY date, partner_id
                    ) AS business_partner_option
--                GROUP BY date, business_partner_code, business_partner_name
--                ORDER BY business_partner_code, date
--                ) AS business_partner_final
            GROUP BY business_partner_code, business_partner_name
            )
        ) AS foo""", [check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
                      check_date, check_date_gte_or_lte, date_gte, check_date_gte_or_lte, date_lte, date_gte, date_lte,
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

        # ===========================================
        # Get context
        # ===========================================
        ctx = self._context.copy()

        # ===========================================
        # Setting init session variables and get domain search
        # ===========================================
        domain = self._get_condition_search_of_module(self=self, args=args)

        # ===========================================
        # If session has no variable (the first runtime)
        # ===========================================
        print_all_button = False
        try:
            print_all_button = request.session['print_all_button_sales_achievement_business']
        except:
            request.session['print_all_button_sales_achievement_business'] = False

        # ===========================================
        # Search If from Advanced Search of Print Button
        # ===========================================
        if ctx.get('have_advance_search') or print_all_button:
            # res = self._search(args=domain, offset=offset, limit=limit, order=order, count=count)
            # return res if count else self.browse(res)
            return super(SalesAchievementBusiness, self).search(domain, offset=offset, limit=limit, order=order, count=count)
        return []

    @staticmethod
    def _get_condition_search_of_module(self, args):
        domain = []
        # current_uid = self._context.get('uid')
        # user = self.env['res.users'].browse(current_uid)
        uid = self.env.uid

        timenow = datetime.datetime.now().strftime('%Y/%m/%d')
        args_init = {'date_gte': '',
                     'date_lte': ''}
        # sales_achievement_business_context = self._context.copy()

        # Save advanced_search_arguments to session
        request.session['advanced_search_arguments_of_business'] = args

        dict_domain_in_search = {
            'business_partner_name_gte': '',
            'business_partner_name_lte': '',
            'business_partner_code_gte': '',
            'business_partner_code_lte': '',
            'tax_class': ''
        }

        # if sales_achievement_business_context and 'sales_achievement_business' in sales_achievement_business_context:
        for record in args:
            if record[0] == '&':
                continue
            if record[0] == 'business_partner_name' and record[1] == '>=':
                args_init['date_gte'] = record[2]
                dict_domain_in_search['business_partner_name_gte'] = record[2]
                continue
            if record[0] == 'business_partner_name' and record[1] == '<=':
                args_init['date_lte'] = record[2]
                dict_domain_in_search['business_partner_name_lte'] = record[2]
                continue
            if (record[0] != 'business_partner_name') and (record[0] != 'tax_class'):
                domain += [record]
            if record[0] == 'business_partner_code' and record[1] == '>=':
                dict_domain_in_search['business_partner_code_gte'] = record[2]
            if record[0] == 'business_partner_code' and record[1] == '<=':
                dict_domain_in_search['business_partner_code_lte'] = record[2]
            if record[0] == 'tax_class':
                dict_domain_in_search['tax_class'] = record[2]

        if args_init['date_gte'] and args_init['date_lte']:
            self.init('date', 'date', args_init['date_gte'], args_init['date_lte'])
        elif args_init['date_gte'] and args_init['date_lte'] == '':
            self.init('date', 'date_gte', args_init['date_gte'], timenow)
        elif args_init['date_lte'] and args_init['date_gte'] == '':
            self.init('date', 'date_lte', timenow, args_init['date_lte'])
        else:
            self.init('nodate', 'date', timenow, timenow)
        args = domain

        # dict_domain_business = {uid: dict_domain_in_search}

        # ===========================================
        # Save advanced_search domain to session
        # ===========================================
        request.session['advanced_search_condition_of_business'] = {uid: dict_domain_in_search}

        return args

    def passConditionInSearchToReport(self):

        # current_uid = self._context.get('uid')
        # user = self.env['res.users'].browse(current_uid)
        uid = self.env.uid

        # ===========================================
        # Get advanced_search domain from session
        # ===========================================
        advanced_search_domain_business = request.session['advanced_search_condition_of_business']
        list_domain = [advanced_search_domain_business[uid]]

        return list_domain

    def print_all_sales_achievement_business(self, args, offset=0, limit=None, order=None, count=False):

        # ==============================================
        # Set session flag to True if from Print Button
        # ==============================================
        request.session['print_all_button_sales_achievement_business'] = True

        # ==============================================
        # Get advanced_search arguments from session
        # ==============================================
        args = request.session['advanced_search_arguments_of_business']

        # ==============================================
        # Get advanced_search arguments has no condition => Don't print
        # ==============================================
        if len(args) == 0:
            request.session['print_all_button_sales_achievement_business'] = False
            return

        # ==============================================
        # Search sales info from view
        # ==============================================
        sales_info_ids = self.search(args)

        # ==============================================
        # Search has record
        # ==============================================
        if len(sales_info_ids) > 0:

            request.session['print_all_button_sales_achievement_business'] = False

            # ==============================================
            # Call report and return
            # ==============================================
            return self.env.ref('Maintain_Achievement_Management.report_sales_achievement_business')\
                .report_action(sales_info_ids, config=False)

        request.session['print_all_button_sales_achievement_business'] = False

        return
