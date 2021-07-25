# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from datetime import datetime, date, timedelta
import calendar, pytz

# initialize global variable
# 対象月日
val_view_date_from = ''
val_view_date_end = ''

val_customer_code_bill_from = ''
val_customer_code_bill_to = ''

# 事業部
val_division = ''
# 営業担当者
val_sales_rep = ''
# 取引先グループ
val_customer_supplier_group_code = ''

# 請求先/得意先コード
val_customer_code_bill = ""
val_customer_code_bill_list = []


class SupplierLedgerInquiryCustom(models.Model):
    _name = 'supplier.ledger'
    _auto = False

    # 日付
    date = fields.Date(string='Date', readonly=True)
    # 伝票Ｎｏ
    invoice_no = fields.Char(string='Invoice No', readonly=True)
    # 取引 / 内訳区分
    invoice_line_type = fields.Char(string='Transaction/Breakdown Category', readonly=True)
    # 得意先コード
    customer_code = fields.Char(string='Customer Code', readonly=True)
    # 請求コード
    customer_code_bill = fields.Char(string='Customer Code Bill', readonly=True)
    # 得意先名
    customer_name = fields.Char(string='Customer Name', readonly=True)
    # JANコード
    jan_code = fields.Char(string='JAN Code', readonly=True)
    # 商品コード
    product_code = fields.Char(string='Product Code', readonly=True)
    # 品番 / 型番
    part_model_number = fields.Char(string='Part/Model Number', readonly=True)
    # メーカー名
    maker_name = fields.Char(string='Maker Name', readonly=True)
    # 商品名
    product_name = fields.Char(string='Product Name', readonly=True)
    # 数量
    quantity = fields.Integer(string='Quantity', readonly=True)

    # 単価
    price_unit = fields.Integer(string='Price Unit', readonly=True)
    # 金額
    price_total = fields.Integer(string='Price Total ', readonly=True)

    # 支払金額
    payment_amount = fields.Integer(string='Payment Amount', readonly=True)

    # 税率
    tax_rate = fields.Integer(string='Tax Rate', readonly=True)
    # Create By User Id
    create_uid = fields.Integer(string='Create By User Id', readonly=True)
    # 税転嫁
    tax_transfer = fields.Char(string='Tax Transfer', readonly=True)

    # partner_id
    partner_id = fields.Integer(string='Partner Id', readonly=True)

    line_level = fields.Integer(readonly=True)

    is_set_color_column = fields.Boolean(string='is_set_color_column', compute='_set_field_color', readonly=True)

    def _compute_residual_amount(self):
        date_before = ''
        date_today = ''

        voucher_before = ''
        voucher_current = ''

        customer_before = ''
        customer_current = ''

        residual_amount_transfer = 0
        residual_amount = 0

        #Calcute residual_amount_before
        residual_amount_first = 0
        residual_amount_before = 0

        is_display_residual_amount_transfer = 1
        is_display_customer = 1
        is_display_payment_class = 1

        is_change_date = 1
        is_change_voucher = 1
        total_invoice_amount = 0
        total_payment_amount = 0

        query = "SELECT * from get_opening_balace_info('" + val_customer_code_bill + "','" + val_view_date_from + "')"
        self._cr.execute(query)
        query_res = self._cr.fetchall()

        for record in query_res:
            residual_amount_first = record[1]

        for record in self:
            date_today = record.date
            voucher_current = record.invoice_no
            customer_current = record.customer_code

            if voucher_current != voucher_before:
                voucher_before = voucher_current
                is_change_voucher = 1
            else:
                is_change_voucher = 0

            if customer_current != customer_before:
                customer_before = customer_current
                is_display_customer = 1
            else:
                is_display_customer = 0


            if date_before == "": #First record
                residual_amount_transfer = residual_amount_first
                residual_amount = residual_amount_first
                is_display_residual_amount_transfer = 1
                is_change_date = 1
            else:
                residual_amount_transfer = residual_amount

            if date_today != date_before:  # Date no change ==> calc last amount
                date_before = date_today
                is_display_residual_amount_transfer = 1
                is_change_date = 1
            else:
                is_display_residual_amount_transfer = 0
                is_change_date = 0
            if record.detail_level != 3:
                residual_amount = residual_amount + record.price_total - record.payment_amount

            if record.detail_level == 0 or record.detail_level == 3:
                is_display_residual_amount = 1
            else:
                is_display_residual_amount = 0
            if record.detail_level == 3 and record.invoice_line_type == '入金':
                is_display_payment_class = 0
            else:
                is_display_payment_class = 1

            if record.product_name == '消費税額(※請求処理)':
                is_display_residual_amount = 1

            if record.detail_level == 3:
                if record.invoice_line_type == '入金': #Total of payment
                    total_payment_amount += record.payment_amount
                else: #Total of Invoice
                    total_invoice_amount += record.price_total

            if record.detail_level == 99:  # Line total
                record.payment_amount_display = total_payment_amount
                record.price_total_display = total_invoice_amount
                is_display_residual_amount = 1
            else:
                record.payment_amount_display = record.payment_amount
                record.price_total_display = record.price_total

            record.residual_amount_transfer = residual_amount_transfer
            record.residual_amount = residual_amount
            record.is_display_residual_amount_transfer = is_display_residual_amount_transfer
            record.is_change_date = is_change_date
            record.is_change_voucher = is_change_voucher
            record.is_display_residual_amount = is_display_residual_amount
            record.is_display_customer = is_display_customer
            record.is_display_payment_class = is_display_payment_class

    # 残高
    residual_amount_transfer = fields.Integer(compute=_compute_residual_amount)
    is_display_residual_amount = fields.Integer(compute=_compute_residual_amount)
    is_display_residual_amount_transfer = fields.Integer(compute=_compute_residual_amount)
    is_display_customer = fields.Integer(compute=_compute_residual_amount)
    is_display_payment_class = fields.Integer(compute=_compute_residual_amount)

    is_change_date = fields.Integer(compute=_compute_residual_amount)
    is_change_voucher = fields.Integer(compute=_compute_residual_amount)
    residual_amount = fields.Integer(compute=_compute_residual_amount)

    price_total_display = fields.Integer(compute=_compute_residual_amount,string='Price Total ')
    payment_amount_display = fields.Integer(compute=_compute_residual_amount,string='Payment Amount')

    detail_level = fields.Integer()



    def _set_display_field(self):
        for record in self:
            record.date_display = record.date
            record.invoice_no_display = record.invoice_no
            record.invoice_line_type_display = record.invoice_line_type
            record.customer_code_display = record.customer_code
            record.customer_code_bill_display = record.customer_code_bill
            record.customer_name_display = record.customer_name
            record.jan_code_display = record.jan_code
            record.product_code_display = record.product_code
            record.part_model_number_display = record.part_model_number
            record.maker_name_display = record.maker_name
            record.product_name_display = record.product_name
            record.quantity_display = record.quantity
            record.price_unit_display = record.price_unit
            record.tax_transfer_display = record.tax_transfer



    # 日付
    date_display = fields.Date(compute=_set_display_field)
    # 伝票Ｎｏ
    invoice_no_display = fields.Char(compute=_set_display_field)
    # 取引 / 内訳区分
    invoice_line_type_display = fields.Char(compute=_set_display_field)
    # 得意先コード
    customer_code_display = fields.Char(compute=_set_display_field)
    # 請求コード
    customer_code_bill_display = fields.Char(compute=_set_display_field)
    # 得意先名
    customer_name_display = fields.Char(compute=_set_display_field)
    # JANコード
    jan_code_display = fields.Char(compute=_set_display_field)
    # 商品コード
    product_code_display = fields.Char(compute=_set_display_field)
    # 品番 / 型番
    part_model_number_display = fields.Char(compute=_set_display_field)
    # メーカー名
    maker_name_display = fields.Char(compute=_set_display_field)
    # 商品名
    product_name_display = fields.Char(compute=_set_display_field)

    # 数量
    quantity_display = fields.Integer(compute=_set_display_field)

    # 単価
    price_unit_display = fields.Integer(compute=_set_display_field)

    # 税転嫁
    tax_transfer_display = fields.Char(compute=_set_display_field)


    # is_display_residual_amount = fields.Integer(compute=_compute_residual_amount)

    # def init(self):
    #     tools.drop_view_if_exists(self._cr, self._table)
    #
    #     # Create data view
    #     self._cr.execute("""
    #     CREATE OR REPLACE VIEW supplier_ledger AS
    #     SELECT row_number() OVER(ORDER BY customer_code, line_level, date, invoice_no, detail_level) AS id, * FROM
    #     (
    #     (
	# 		SELECT NULL AS date,
    #         '' AS invoice_no,
    #         0 AS detail_level,
    #         0 AS line_level,
    #         '' AS invoice_line_type,
    #         res_partner.customer_code,
    #         res_partner.name AS customer_name,
    #         '' AS jan_code,
    #         '' AS product_code,
    #         '' AS part_model_number,
    #         '' AS maker_name,
    #         '繰越残高' AS product_name,
    #         0 AS quantity,
    #         0 AS price_unit,
    #         0 AS price_total,
    #         0 AS payment_amount,
    #         0 AS tax_rate,
    #         res_partner.create_uid,
    #         '' AS tax_transfer,
    #         res_partner.id AS partner_id,
    #         res_partner.customer_code_bill,
    #             CASE
    #                 WHEN res_partner.customer_code <> res_partner.customer_code_bill THEN 1
    #                 WHEN res_partner.customer_code = res_partner.customer_code_bill THEN 0
    #                 ELSE NULL::integer
    #             END AS isbill_place
    #        FROM res_partner
    #       WHERE res_partner.active = true AND ((res_partner.id IN ( SELECT account_move.partner_id
    #                FROM account_move
    #               WHERE account_move.type = 'out_invoice' AND account_move.state = 'posted')) OR (res_partner.id IN ( SELECT account_payment.partner_id
    #                FROM account_payment)))
    #     )
	# 	UNION ALL
    #     (
	# 		SELECT account_move_line.date,
    #         account_move_line.invoice_no,
    #         1 AS detail_level,
    #         1 AS line_level,
    #         account_move_line.x_invoicelinetype AS invoice_line_type,
    #         res_partner.customer_code,
    #         res_partner.name AS customer_name,
    #         account_move_line.product_barcode AS jan_code,
    #         account_move_line.product_code,
    #         account_move_line.invoice_custom_standardnumber AS part_model_number,
    #         account_move_line.product_maker_name AS maker_name,
    #         account_move_line.product_name,
    #         account_move_line.quantity,
    #         account_move_line.price_unit,
    #         account_move_line.price_total,
    #         0 AS payment_amount,
    #         account_move_line.tax_rate,
    #         account_move_line.create_uid,
    #             CASE
    #                 WHEN account_move_line.x_tax_transfer_show_tree = 'foreign_tax' THEN '外税／明細'
    #                 WHEN account_move_line.x_tax_transfer_show_tree = 'internal_tax' THEN '内税／明細'
    #                 WHEN account_move_line.x_tax_transfer_show_tree = 'voucher' THEN '伝票'
    #                 WHEN account_move_line.x_tax_transfer_show_tree = 'invoice' THEN '請求'
    #                 WHEN account_move_line.x_tax_transfer_show_tree = 'custom_tax' THEN '税調整別途'
    #                 ELSE NULL
    #             END AS tax_transfer,
    #         res_partner.id AS partner_id,
    #         res_partner.customer_code_bill,
    #             CASE
    #                 WHEN res_partner.customer_code <> res_partner.customer_code_bill THEN 1
    #                 WHEN res_partner.customer_code = res_partner.customer_code_bill THEN 0
    #                 ELSE NULL::integer
    #             END AS isbill_place
    #        FROM account_move_line
    #          LEFT JOIN res_partner ON res_partner.id = account_move_line.partner_id AND res_partner.active = true
    #       WHERE account_move_line.account_internal_type <> 'receivable' AND account_move_line.exclude_from_invoice_tab = false AND account_move_line.parent_state = 'posted'
    #     UNION ALL
    #      SELECT account_move.x_studio_date_invoiced AS date,
    #         account_move.x_studio_document_no AS invoice_no,
    #         2 AS detail_level,
    #         1 AS line_level,
    #         '' AS invoice_line_type,
    #         res_partner.customer_code,
    #         res_partner.name AS customer_name,
    #         '' AS jan_code,
    #         '' AS product_code,
    #         '' AS part_model_number,
    #         '' AS maker_name,
    #         '消費税額' AS product_name,
    #         0 AS quantity,
    #         0 AS price_unit,
    #         account_move.x_voucher_tax_amount AS price_total,
    #         0 AS payment_amount,
    #         0,
    #         account_move.create_uid,
    #         '' AS tax_transfer,
    #         res_partner.id AS partner_id,
    #         res_partner.customer_code_bill,
    #             CASE
    #                 WHEN res_partner.customer_code <> res_partner.customer_code_bill THEN 1
    #                 WHEN res_partner.customer_code = res_partner.customer_code_bill THEN 0
    #                 ELSE NULL::integer
    #             END AS isbill_place
    #        FROM account_move
    #          LEFT JOIN res_partner ON res_partner.id = account_move.partner_id AND res_partner.active = true
    #       WHERE account_move.type = 'out_invoice' AND account_move.state = 'posted'
	# 	)
    #     UNION ALL
	# 	(
    #      SELECT account_move.x_studio_date_invoiced AS date,
    #         account_move.x_studio_document_no AS invoice_no,
    #         3 AS detail_level,
    #         1 AS line_level,
    #         '' AS invoice_line_type,
    #         res_partner.customer_code,
    #         res_partner.name AS customer_name,
    #         '' AS jan_code,
    #         '' AS product_code,
    #         '' AS part_model_number,
    #         '' AS maker_name,
    #         '伝票計' AS product_name,
    #         0 AS quantity,
    #         0 AS price_unit,
    #         account_move.amount_total AS price_total,
    #         0 AS payment_amount,
    #         0,
    #         account_move.create_uid,
    #         '' AS tax_transfer,
    #         res_partner.id AS partner_id,
    #         res_partner.customer_code_bill,
    #             CASE
    #                 WHEN res_partner.customer_code <> res_partner.customer_code_bill THEN 1
    #                 WHEN res_partner.customer_code = res_partner.customer_code_bill THEN 0
    #                 ELSE NULL::integer
    #             END AS isbill_place
    #        FROM account_move
    #          LEFT JOIN res_partner ON res_partner.id = account_move.partner_id AND res_partner.active = true
    #       WHERE account_move.type = 'out_invoice' AND account_move.state = 'posted'
    #     )
	# 	UNION ALL
	# 	(
	# 	SELECT account_payment.payment_date,
    #         account_payment.name,
    #         3 AS detail_level,
    #         1 AS line_level,
    #         '入金' AS "varchar",
    #         res_partner.customer_code,
    #         res_partner.name,
    #         '' AS "varchar",
    #         '' AS "varchar",
    #         NULL AS "varchar",
    #         '' AS "varchar",
    #         '伝票計' AS product_name,
    #         0,
    #         0,
    #         0,
    #         account_payment.amount,
    #         0,
    #         account_payment.create_uid,
    #         '' AS text,
    #         res_partner.id,
    #         res_partner.customer_code_bill,
    #             CASE
    #                 WHEN res_partner.customer_code <> res_partner.customer_code_bill THEN 1
    #                 WHEN res_partner.customer_code = res_partner.customer_code_bill THEN 0
    #                 ELSE NULL::integer
    #             END AS isbill_place
    #        FROM account_payment
    #          LEFT JOIN res_partner ON res_partner.id = account_payment.partner_id AND res_partner.active = true
	# 	)
	# 	UNION ALL
	# 	(
	# 	SELECT account_payment.payment_date,
    #         account_payment.name,
    #         1 AS detail_level,
    #         1 AS line_level,
    #         '入金' AS "varchar",
    #         res_partner.customer_code,
    #         res_partner.name,
    #         '' AS "varchar",
    #         '' AS "varchar",
    #         NULL AS "varchar",
    #         '' AS "varchar",
    #         receipt_divide_custom.name,
    #         0,
    #         0,
    #         0,
    #         account_payment_line.payment_amount,
    #         0,
    #         account_payment.create_uid,
    #         '' AS text,
    #         res_partner.id,
    #         res_partner.customer_code_bill,
    #             CASE
    #                 WHEN res_partner.customer_code <> res_partner.customer_code_bill THEN 1
    #                 WHEN res_partner.customer_code = res_partner.customer_code_bill THEN 0
    #                 ELSE NULL::integer
    #             END AS isbill_place
    #        FROM account_payment
    #          LEFT JOIN account_payment_line ON account_payment.id = account_payment_line.payment_id
    #          LEFT JOIN receipt_divide_custom ON account_payment_line.receipt_divide_custom_id = receipt_divide_custom.id
    #          LEFT JOIN res_partner ON res_partner.id = account_payment.partner_id AND res_partner.active = true
	# 	)) AS foo""")

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
            Overriding function search from file models.py
            File path Override: /odoo/models.py
        """
        domain = self._get_condition_search_of_module(self=self, args=args)
        if len(domain) > 0:
            res = self._search(args=domain, offset=offset, limit=limit, order=order, count=count)
            return res if count else self.browse(res)

    @staticmethod
    def _get_condition_search_of_module(self, args):
        """
            Get condition search of module
        """
        domain = []
        domain_res_partner = []
        domain_hr_employee = []
        supplier_ledger_inquiry_context = self._context.copy()
        if supplier_ledger_inquiry_context and 'supplier_ledger_inquiry_module' in supplier_ledger_inquiry_context:
            # using global keyword
            global val_view_date_from
            global val_view_date_to
            global val_customer_code_bill
            global val_customer_code_bill_list
            global val_division
            global val_sales_rep
            global val_customer_supplier_group_code

            # reset global keyword
            val_division = ''
            check_required_field = False
            val_view_date_from = ""
            val_view_date_to = ""
            val_customer_code_bill = ""
            val_customer_code_bill_list.clear()

            # Check required field
            if 'customer_code_bill' in (item for sublist in args for item in sublist):
                check_required_field = True

            if check_required_field:
                for record in args:
                    if record[0] == '&':
                        continue
                    if record[0] == 'date':
                        if len(record[1]) > 0 and len(val_view_date_from) == 0:
                            val_view_date_from = record[2]
                            # domain += ['|', ('date', '>=', val_view_date_from), [('line_level', '=', 0), ('customer_code','=','1000045')]]
                            # # record = [['|', ('date', '>=', val_view_date_from), ('line_level', '=', 0)]]
                        else:
                            val_view_date_to = record[2]
                            # # record = [['|', ('date', '<=', val_view_date_to), ('line_level', '=', 0)]]
                            # domain += ['|', ('date', '<=', val_view_date_to), [('line_level', '=', 0), ('customer_code','=','1000045')]]
                        check_input_date = 1
                        continue

                    if record[0] == 'customer_code_bill':
                        # Get child code list
                        domain_res_partner += [('customer_code_bill', '=', str(record[2]).upper())]
                        res_partner_ids = self.env["res.partner"].search(domain_res_partner)
                        val_customer_code_bill = str(record[2]).upper()
                        val_customer_code_bill_list.append(val_customer_code_bill)  # First parent code
                        for row in res_partner_ids:
                            if row.customer_code:
                                val_customer_code_bill_list.append(row.customer_code)
                        # domain += [('customer_code', 'in', val_customer_code_bill_list)]
                    continue


                a = ('customer_code', 'in', val_customer_code_bill_list)
                if len(val_view_date_from) == 0:
                    val_view_date_from = '1900-01-01'

                if len(val_view_date_to) == 0:
                    val_view_date_to = datetime.now().strftime("%Y-%m-%d")

                b = ('date', '>=', val_view_date_from)
                c = ('line_level', 'in', ['0','99'])
                d = ('customer_code', '=', val_customer_code_bill)
                e = ('date', '<=', val_view_date_to)

                # a and (b or (c and d ) and (e or (c and d)) ==> '&','&', a,'|', b,'&', c, d, '|', e, '&', c, d
                domain = ['&','&', a,'|', b,'&', c, d, '|', e, '&', c, d]




            # filter division and sales_rep from table res_partner
            if len(domain_hr_employee) > 0:
                hr_employee_ids = self.env["hr.employee"].search(domain_hr_employee)
                user_id = []
                for row in hr_employee_ids:
                    if row.user_id.id:
                        user_id.append(row.user_id.id)
                if len(user_id) > 0:
                    domain += [('create_uid', 'in', user_id)]
                else:
                    domain += [('create_uid', '=', False)]
        else:
            domain = args
        return domain

    # def _get_closing_date(self, year_month_selected):
    #     """
    #         Get closing date of company
    #     """
    #     # using global keyword
    #     global val_target_month
    #     # get information closing date
    #     customer_closing_date = self._get_company_closing_date()
    #     _start = 1
    #     if customer_closing_date:
    #         _start = customer_closing_date
    #
    #     if year_month_selected:
    #         # set date when input condition
    #         selected_date = datetime.strptime(year_month_selected, '%Y-%m').date()
    #     else:
    #         # set current date
    #         selected_date = datetime.now().astimezone(pytz.timezone(self.env.user.tz))
    #         val_target_month = selected_date.strftime("%Y-%m")
    #
    #     # get closing date of year_month_selected
    #     if _start >= 28:
    #         # get days in month
    #         days_in_month = calendar.monthrange(selected_date.year, selected_date.month)[1]
    #         # set closing date start
    #         _closing_date_start = selected_date.replace(day=1)
    #         # set closing date end
    #         _closing_date_end = selected_date.replace(day=days_in_month)
    #     else:
    #         # set closing date end
    #         _closing_date_end = selected_date.replace(day=_start)
    #         # get day of closing_date_start from day of closing_date_end
    #         day_closing_date_start = _closing_date_end.day + 1
    #         # get year/month of closing_date_start from year/month of closing_date_end
    #         if _closing_date_end.month == 1:
    #             month_closing_date_start = 12
    #             year_closing_date_start = _closing_date_end.year - 1
    #         else:
    #             month_closing_date_start = _closing_date_end.month - 1
    #             year_closing_date_start = _closing_date_end.year
    #         # set closing date start
    #         _closing_date_start = _closing_date_end.replace(year=year_closing_date_start,
    #                                                         month=month_closing_date_start, day=day_closing_date_start)
    #
    #     closing_date = {
    #         'closing_date_start': _closing_date_start,
    #         'closing_date_end': _closing_date_end
    #     }
    #
    #     return closing_date

    @api.constrains('id')
    def _get_value_condition_input(self):
        """
            Get value condition input from advanced search
        """
        for item in self:
            # set the value to use for the program report
            # item.input_target_month = datetime.strptime(val_target_month, '%Y-%m').strftime('%Y年%m月')
            item.input_customer_code_bill_from = val_customer_code_bill_from
            item.input_customer_code_bill_to = val_customer_code_bill_to
            item.input_division = val_division
            item.input_sales_rep = val_sales_rep
            item.input_customer_supplier_group_code = val_customer_supplier_group_code

    def _get_company_closing_date(self):
        """
            Get closing date from res_company
        """
        # get closing date from res_company
        company_closing_date = self.env['res.users'].search([['id', '=', self.env.uid]]).company_id.company_closing_date
        # return day closing
        return company_closing_date


    def _format_data_number(self):
        for record in self:
            if record.quantity == 0:
                record.quantity_display = ''
            else:
                record.quantity_display = str(record.quantity)

    def _set_field_color(self):
        for record in self:
            if record.invoice_line_type == "入金":
                record.is_set_color_column = True
            else:
                record.is_set_color_column = False
