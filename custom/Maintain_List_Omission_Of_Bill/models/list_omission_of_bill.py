# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from datetime import datetime

# initialize global variable
# 締日（締日グループ）
val_start_day = ''
# 売上日
val_sales_date = ''
# 事業部
val_division = ''
# 営業担当者
val_sales_rep = ''
# 取引先グループ
val_customer_supplier_group_code = ''
# 請求先
val_customer_code_bill_from = ''
val_customer_code_bill_to = ''
# 発行形式
val_issue_format = '0'


class ListOmissionOfBill(models.Model):
    _name = 'omission.bill'
    _auto = False

    # 売上日付
    sales_date = fields.Date('Sales Date')
    # 伝票Ｎｏ
    invoice_no = fields.Char('Invoice No')
    # 得意先名
    customer_name = fields.Char('Customer Name')
    # 伝票合計額
    amount_untaxed = fields.Float('Amount Untaxed')
    # 消費税額
    amount_tax = fields.Float('Amount Tax')
    # 明細数
    detail_number = fields.Integer('Number Of Items')
    # 取引/内訳区分
    invoice_line_type = fields.Char('Transaction/Breakdown Category')
    # JANコード
    jan_code = fields.Char('JAN Code')
    # 商品コード
    product_code = fields.Char('Product Code')
    # 品番/型番
    part_model_number = fields.Char('Part/Model Number')
    # メーカー名
    maker_name = fields.Char('Maker Name')
    # 商品名
    product_name = fields.Char('Product Name')
    # 数量
    quantity = fields.Float('Quantity')
    # 単位
    unit = fields.Char('Unit')
    # 単価
    price_unit = fields.Float('Price Unit')
    # 金額
    price_total = fields.Float('Price Total')
    # 税率
    tax_rate = fields.Float('Tax Rate')
    # 税転嫁
    tax_transfer = fields.Char('Tax Transfer')

    # the marker id is the voucher in the table iew
    id_voucher = fields.Integer('Id Voucher')
    # 締日
    start_day = fields.Integer('Closing Day')
    closing_date_name = fields.Char('Closing Date Name')
    # 事業部
    department_id = fields.Integer('Division')
    department_name = fields.Char('Division Name')
    # 営業担当者
    sales_rep = fields.Integer('Sales Representative')
    sales_rep_name = fields.Char('Sales Representative Name')
    # 取引先グループ
    customer_supplier_group_code = fields.Integer('Customer Supplier Group Code')
    customer_supplier_group_name = fields.Char('Customer Supplier Group Name')
    # 請求先
    customer_code_bill = fields.Char('Customer Code Bill')

    # fields input condition advanced search
    # 締日（締日グループ）
    input_start_day = fields.Char('Input Closing Day', compute='_compute_fields', default='', store=False)
    # 売上日
    input_sales_date = fields.Char('Sales Date', compute='_compute_fields', default='', store=False)
    # 事業部
    input_division = fields.Char('Division', compute='_compute_fields', default='', store=False)
    # 営業担当者
    input_sales_rep = fields.Char('Sales Representative', compute='_compute_fields', default='', store=False)
    # 取引先グループ
    input_customer_supplier_group_code = fields.Char('Customer Supplier Group Code', compute='_compute_fields',
                                                     default='', store=False)
    # 請求先From
    input_customer_code_bill_from = fields.Char('Customer Code Bill From', compute='_compute_fields', default='',
                                                store=False)
    # 請求先To
    input_customer_code_bill_to = fields.Char('Customer Code Bill To', compute='_compute_fields', default='',
                                              store=False)
    # 発行形式
    input_issue_format = fields.Char('Issue Format', compute='_compute_fields', default='0', store=False)
    input_issue_format_str = fields.Char('Issue Format String', compute='_compute_fields', default='伝票単位', store=False)

    amount_untaxed_int_format = fields.Integer(string='Amount Untaxed', compute='_amount_untaxed_int_format'
                                               , readonly=True)

    amount_tax_int_format = fields.Integer(string='Amount Tax', compute='_amount_tax_int_format', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
        CREATE OR REPLACE VIEW omission_bill AS
            SELECT row_number() OVER(ORDER BY sales_date) AS id , * FROM(
                (		
                    SELECT
                    row_number() OVER(PARTITION BY account_move_line.move_id ORDER BY account_move_line.move_id) AS id_voucher,
                    account_move.x_studio_date_invoiced AS sales_date, -- 売上日付
                    account_move.x_studio_document_no AS invoice_no, -- 伝票Ｎｏ
                    res_partner.NAME AS customer_name, -- 得意先名
                    sum( account_move.amount_untaxed ) AS amount_untaxed, -- 伝票合計額
                    sum( account_move.amount_tax ) AS amount_tax, -- 消費税額
                    count (account_move_line.id) OVER (PARTITION BY account_move.NAME) AS detail_number, -- 明細数
                    account_move_line.x_invoicelinetype AS invoice_line_type, -- 取引/内訳区分
                    account_move_line.product_barcode AS jan_code, -- JANコード
                    account_move_line.product_code AS product_code, -- 商品コード
                    account_move_line.invoice_custom_standardnumber AS part_model_number, -- 品番/型番
                    account_move_line."product_maker_name" AS maker_name, -- メーカー名
                    account_move_line.product_name AS product_name, -- 商品名
                    account_move_line.quantity, -- 数量
                    account_move_line.product_uom_id AS unit, -- 単位
                    account_move_line.price_unit, -- 単価
                    account_move_line.price_total, -- 金額
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
                    CASE
                        WHEN account_move.x_voucher_tax_transfer = 'foreign_tax' THEN
                            '外税／明細'
                        WHEN account_move.x_voucher_tax_transfer = 'internal_tax' THEN
                            '内税／明細'
                        WHEN account_move.x_voucher_tax_transfer = 'voucher' THEN
                            '伝票'
                        WHEN account_move.x_voucher_tax_transfer = 'invoice' THEN 
                            '請求'
                        WHEN account_move.x_voucher_tax_transfer = 'custom_tax' THEN 
                            '税調整別途'  
                    END AS tax_transfer, -- 税転嫁（外／内／非、明／伝／請）
                    closing_date.start_day,
                    closing_date.name as closing_date_name,
                    hr_department.id AS department_id,
                    hr_department.name AS department_name,
                    account_move.sales_rep,
					hr_employee.name AS sales_rep_name,
                    res_partner.customer_supplier_group_code,
                    business_partner_group_custom.name AS customer_supplier_group_name,
                    res_partner.customer_code_bill
                    FROM
                        account_move
                        INNER JOIN res_partner ON res_partner.id = account_move.partner_id
                                                AND res_partner.active = True
                        INNER JOIN account_move_line ON account_move.id = account_move_line.move_id
                                                AND account_move_line.account_internal_type != 'receivable'
                                                AND account_move_line.exclude_from_invoice_tab = False
                        INNER JOIN closing_date ON res_partner.customer_closing_date = closing_date.id
                                                AND closing_date.active = True
                        INNER JOIN hr_employee ON hr_employee.id = account_move.sales_rep
                                                AND hr_employee.active = True
                        INNER JOIN hr_department ON hr_department.id = hr_employee.department_id
                                                AND hr_department.active = True
                        INNER JOIN business_partner_group_custom ON business_partner_group_custom.id = res_partner.customer_supplier_group_code
                                                AND business_partner_group_custom.active = True
                    WHERE
                        account_move.bill_status = 'not yet'
                        AND account_move.state = 'posted' 
                        AND account_move.invoice_payment_state = 'not_paid' 
       /*                 AND (
                            ( account_move.x_studio_date_invoiced <= date_trunc ( 'month', CURRENT_DATE ) :: DATE + closing_date.start_day - 1 )
                            OR (
                                closing_date.start_day >= 28 AND 
                                date_trunc ( 'month', CURRENT_DATE ) = date_trunc ( 'month', account_move.x_studio_date_invoiced )
                            )
                        )*/
                    GROUP BY
                        account_move.x_studio_date_invoiced,
                        account_move.name,
                        account_move.x_studio_document_no,
                        res_partner.NAME,
                        account_move_line.id,
                        hr_employee.department_id,
                        account_move_line.x_invoicelinetype,
                        account_move_line.product_barcode,
                        account_move_line.product_code,
                        account_move_line.invoice_custom_standardnumber,
                        account_move_line."product_maker_name",
                        account_move_line.product_name,
                        account_move_line.quantity,
                        account_move_line.product_uom_id,
                        account_move_line.price_unit,
                        account_move_line.price_total,
                        account_move_line.tax_repartition_line_id,
                        account_move.x_voucher_tax_transfer,
                        closing_date.start_day,
						closing_date.name,
						hr_department.id,
						hr_department.name,
                        account_move.sales_rep,
						hr_employee.name,
                        res_partner.customer_supplier_group_code,
                        business_partner_group_custom.name,
                        res_partner.customer_code_bill
            ) ) AS foo""")

    @api.constrains('sales_date')
    def _compute_fields(self):
        """
            Compute Fields
        """
        for item in self:
            item.input_start_day = val_start_day
            if val_sales_date:
                item.input_sales_date = datetime.strptime(val_sales_date, '%Y-%m-%d').strftime('%Y年%m月%d日')
            else:
                item.input_sales_date = val_sales_date
            item.input_division = val_division
            item.input_sales_rep = val_sales_rep
            item.input_customer_supplier_group_code = val_customer_supplier_group_code
            item.input_customer_code_bill_from = val_customer_code_bill_from
            item.input_customer_code_bill_to = val_customer_code_bill_to
            item.input_issue_format = val_issue_format
            if val_issue_format == '0':
                item.input_issue_format_str = '伝票単位'
            elif val_issue_format == '1':
                item.input_issue_format_str = '明細単位'

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
            Overriding function search from file models.py
            File path Override: /odoo/models.py
        """
        # using global keyword
        global val_start_day
        global val_sales_date
        global val_division
        global val_sales_rep
        global val_customer_supplier_group_code
        global val_customer_code_bill_from
        global val_customer_code_bill_to
        global val_issue_format
        # reset global keyword
        val_start_day = 1
        val_sales_date = ''
        val_division = ''
        val_sales_rep = ''
        val_customer_supplier_group_code = ''
        val_customer_code_bill_from = ''
        val_customer_code_bill_to = ''
        val_issue_format = '0'

        module_context = self._context.copy()
        if module_context.get('have_advance_search') and module_context.get('list_omission_of_bill_module'):
            domain = []
            # arr = ["division", "sales_rep", "customer_supplier_group_code"]
            # check = 0
            for record in args:
                if record[0] == '&':
                    continue
                # if record[0] == 'search_category' and record[2] == 'equal':
                #     check = 1
                # if check == 1 and record[0] in arr:
                #     record[1] = '=ilike'
                if 'closing_date' == record[0]:
                    val_start_day = record[2]
                    if record[2].isnumeric():
                        record[0] = 'start_day'
                        record[1] = '='
                    else:
                        record[0] = 'closing_date_name'
                if 'sales_date' == record[0]:
                    val_sales_date = record[2]
                if 'division' == record[0]:
                    val_division = record[2]
                    if record[2].isnumeric():
                        record[0] = 'department_id'
                        record[1] = '='
                    else:
                        record[0] = 'department_name'
                if 'sales_rep' == record[0]:
                    val_sales_rep = record[2]
                    if record[2].isnumeric():
                        record[0] = 'sales_rep'
                        record[1] = '='
                    else:
                        record[0] = 'sales_rep_name'
                if 'customer_supplier_group_code' == record[0]:
                    val_customer_supplier_group_code = record[2]
                    if record[2].isnumeric():
                        record[0] = 'customer_supplier_group_code'
                        record[1] = '='
                    else:
                        record[0] = 'customer_supplier_group_name'
                if 'customer_code_bill_from' == record[0]:
                    val_customer_code_bill_from = record[2]
                    record[0] = 'customer_code_bill'
                if 'customer_code_bill_to' == record[0]:
                    val_customer_code_bill_to = record[2]
                    record[0] = 'customer_code_bill'
                if 'issue_format' == record[0]:
                    val_issue_format = record[2]
                    continue
                # if record[0] != 'search_category':
                domain += [record]
            if val_issue_format == '0':
                domain += [['id_voucher', '=', 1]]
            args = domain

        if (len(args) == 1 and val_issue_format == '0') or len(args) == 0:
            return []
        res = super(ListOmissionOfBill, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res

    def _amount_untaxed_int_format(self):
        for rec in self:
            rec.amount_untaxed_int_format = int(rec.amount_untaxed)

    def _amount_tax_int_format(self):
        for rec in self:
            rec.amount_tax_int_format = int(rec.amount_tax)

