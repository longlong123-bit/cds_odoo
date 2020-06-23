# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from datetime import datetime, date, timedelta
import calendar

# initialize global variable
# 対象月
val_target_month = ''
# 請求先
val_customer_code_bill_from = ''
val_customer_code_bill_to = ''
# 事業部
val_division = ''
# 営業担当者
val_sales_rep = ''
# 取引先グループ
val_customer_supplier_group_code = ''


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
    customer_code = fields.Integer(string='Customer Code', readonly=True)
    # 得意先名
    customer_name = fields.Char(string='Customer Name', readonly=True)
    # JANコード
    jan_code = fields.Char(string='JAN Code', readonly=True)
    # 商品コード
    product_code = fields.Integer(string='Product Code', readonly=True)
    # 品番 / 型番
    part_model_number = fields.Char(string='Part/Model Number', readonly=True)
    # メーカー名
    maker_name = fields.Char(string='Maker Name', readonly=True)
    # 商品名
    product_name = fields.Char(string='Product Name', readonly=True)
    # 数量
    quantity = fields.Float(string='Quantity', readonly=True)
    # 単価
    price_unit = fields.Float(string='Price Unit', readonly=True)
    # 金額
    price_total = fields.Float(string='Price Total ', readonly=True)
    # 支払金額
    payment_amount = fields.Float(string='Payment Amount', readonly=True)
    # 税率
    tax_rate = fields.Float(string='Tax Rate', readonly=True)
    # Create By User Id
    create_uid = fields.Integer(string='Create By User Id', readonly=True)
    # 税転嫁
    tax_transfer = fields.Char(string='Tax Transfer', readonly=True)

    # fields input condition advanced search
    input_target_month = fields.Char('Input Target Date', compute='_get_value_condition_input', default='', store=False)
    input_customer_code_bill_from = fields.Char('Input Customer Code Bill From', compute='_get_value_condition_input',
                                                default='',
                                                store=False)
    input_customer_code_bill_to = fields.Char('Input Customer Code Bill To', compute='_get_value_condition_input', default='',
                                              store=False)
    input_division = fields.Char('Input Division', compute='_get_value_condition_input', default='', store=False)
    input_sales_rep = fields.Char('Input Sales Representative', compute='_get_value_condition_input', default='', store=False)
    input_customer_supplier_group_code = fields.Char('Input Customer Supplier Group Code',
                                                     compute='_get_value_condition_input', default='', store=False)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
        CREATE OR REPLACE VIEW supplier_ledger AS
        SELECT row_number() OVER(ORDER BY date) AS id , * FROM(
            (SELECT
                account_move_line.date, -- 日付
                account_move_line.invoice_no, -- 伝票Ｎｏ
                account_move_line.x_invoicelinetype AS invoice_line_type, -- 取引/内訳区分
                account_move_line.partner_id AS customer_code, -- 得意先コード
                res_partner.name AS customer_name, -- 得意先名
                account_move_line.x_product_barcode AS jan_code, -- JANコード
                account_move_line.product_id AS product_code, -- 商品コード
                account_move_line.invoice_custom_standardnumber AS part_model_number, -- 品番/型番
                account_move_line."invoice_custom_FreightCategory" AS maker_name, -- メーカー名
                account_move_line.x_product_name AS product_name, -- 商品名
                account_move_line.quantity, -- 数量
                account_move_line.price_unit, -- 単価
                account_move_line.price_total, -- 金額
                0 as payment_amount,
                CASE
                        WHEN account_move_line.price_total - account_move_line.price_subtotal <= 0 THEN
                            0
                        ELSE
                            CASE
                                WHEN (account_move_line.price_subtotal * 0.1) = (account_move_line.price_total - account_move_line.price_subtotal) THEN
                                    10
                                ELSE
                                    5
                            END
                END AS tax_rate, -- 税率
                account_move_line.create_uid,
                CASE
                    WHEN account_move_line.x_tax_transfer_show_tree = 'foreign_tax' THEN
                        '外税／明細'
                    WHEN account_move_line.x_tax_transfer_show_tree = 'internal_tax' THEN
                        '内税／明細'
                    WHEN account_move_line.x_tax_transfer_show_tree = 'voucher' THEN
                        '伝票'
                    WHEN account_move_line.x_tax_transfer_show_tree = 'invoice' THEN 
                        '請求'
                    WHEN account_move_line.x_tax_transfer_show_tree = 'custom_tax' THEN 
                        '税調整別途'  
                END AS tax_transfer -- 税転嫁（外／内／非、明／伝／請）
            FROM
                account_move_line
                    LEFT JOIN
                        res_partner
                            ON res_partner.id = account_move_line.partner_id
                            AND res_partner.active = true
            WHERE
                account_move_line.account_internal_type != 'receivable'
                AND account_move_line.exclude_from_invoice_tab = False
                AND account_move_line.parent_state = 'posted'
            )
            UNION (
                SELECT
                    account_payment.payment_date,
                    account_payment.name,
                    '入金',
                    account_payment.partner_id,
                    res_partner.name,
                    '',
                    0,
                    NULL, -- 品番/型番
                    '', -- メーカー名
                    '',
                    0,
                    0,
                    0,
                    account_payment.payment_amount,
                    0,
                    account_payment.create_uid,
                    '' -- 税転嫁（外／内／非、明／伝／請）
                FROM
                    account_payment
                        LEFT JOIN
                            res_partner
                                ON res_partner.id = account_payment.partner_id
                                AND res_partner.active = true
            ) ) AS foo""")

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
        """
            Get condition search of module
        """
        domain = []
        domain_res_partner = []
        domain_hr_employee = []
        supplier_ledger_inquiry_context = self._context.copy()
        if supplier_ledger_inquiry_context and 'supplier_ledger_inquiry_module' in supplier_ledger_inquiry_context:
            # using global keyword
            global val_target_month
            global val_customer_code_bill_from
            global val_customer_code_bill_to
            global val_division
            global val_sales_rep
            global val_customer_supplier_group_code
            # reset global keyword
            val_target_month = ''
            val_customer_code_bill_from = ''
            val_customer_code_bill_to = ''
            val_division = ''
            val_sales_rep = ''
            val_customer_supplier_group_code = ''

            for record in args:
                if record[0] == '&':
                    continue
                if record[0] == 'target_month':
                    val_target_month = record[2]
                    continue
                if record[0] == 'customer_code_bill_from':
                    record[0] = 'customer_code_bill'
                    domain_res_partner += [record]
                    val_customer_code_bill_from = record[2]
                    continue
                if record[0] == 'customer_code_bill_to':
                    record[0] = 'customer_code_bill'
                    domain_res_partner += [record]
                    val_customer_code_bill_to = record[2]
                    continue
                if record[0] == 'division':
                    record[0] = 'department_id'
                    record[2] = int(record[2])
                    domain_hr_employee += [record]
                    val_division = record[2]
                    continue
                if record[0] == 'sales_rep':
                    record[0] = 'id'
                    record[2] = int(record[2])
                    domain_hr_employee += [record]
                    val_sales_rep = record[2]
                    continue
                if record[0] == 'customer_supplier_group_code':
                    record[2] = int(record[2])
                    domain_res_partner += [record]
                    val_customer_supplier_group_code = record[2]
                    continue

                domain += [record]

            # get closing current date
            closing_date = self._get_closing_date(year_month_selected=val_target_month)
            closing_date_start = closing_date['closing_date_start']
            closing_date_end = closing_date['closing_date_end']
            domain += [('date', '>=', str(closing_date_start))]
            domain += [('date', '<=', str(closing_date_end))]

            # filter customer_code_bill and customer_supplier_group_code from table res_partner
            if len(domain_res_partner) > 0:
                res_partner_ids = self.env["res.partner"].search(domain_res_partner)
                partner_ids = []
                for row in res_partner_ids:
                    if row.id:
                        partner_ids.append(row.id)
                if len(partner_ids) > 0:
                    domain += [('partner_id', 'in', partner_ids)]
                else:
                    domain += [('partner_id', '=', False)]

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

    def _get_closing_date(self, year_month_selected):
        """
            Get closing date of company
        """
        # using global keyword
        global val_target_month
        # get information closing date
        customer_closing_date = self._get_company_closing_date()
        _start = 1
        if customer_closing_date:
            _start = customer_closing_date

        if year_month_selected:
            # set date when input condition
            selected_date = datetime.strptime(year_month_selected, '%Y-%m').date()
        else:
            # set current date
            selected_date = date.today()
            val_target_month = selected_date.strftime("%Y-%m")

        # get closing date of year_month_selected
        if _start >= 28:
            # get days in month
            days_in_month = calendar.monthrange(selected_date.year, selected_date.month)[1]
            # set closing date start
            _closing_date_start = selected_date.replace(day=1)
            # set closing date end
            _closing_date_end = selected_date.replace(day=days_in_month)
        else:
            # set closing date end
            _closing_date_end = selected_date.replace(day=_start)
            # get day of closing_date_start from day of closing_date_end
            day_closing_date_start = _closing_date_end.day + 1
            # get year/month of closing_date_start from year/month of closing_date_end
            if _closing_date_end.month == 1:
                month_closing_date_start = 12
                year_closing_date_start = _closing_date_end.year - 1
            else:
                month_closing_date_start = _closing_date_end.month - 1
                year_closing_date_start = _closing_date_end.year
            # set closing date start
            _closing_date_start = _closing_date_end.replace(year=year_closing_date_start,
                                                            month=month_closing_date_start, day=day_closing_date_start)

        closing_date = {
            'closing_date_start': _closing_date_start,
            'closing_date_end': _closing_date_end
        }

        return closing_date

    @api.constrains('id')
    def _get_value_condition_input(self):
        """
            Get value condition input from advanced search
        """
        for item in self:
            # set the value to use for the program report
            item.input_target_month = val_target_month
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