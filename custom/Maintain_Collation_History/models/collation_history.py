# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools

class CollationPayment(models.Model):
    _inherit = 'bill.info'

    def _get_customer_other_cd(self):
        for cd in self:
            # if self.partner_id:
            cd.customer_other_cd = cd.partner_id.customer_other_cd

    def get_detail(self):
        # records = self.env['bill.invoice.details'].search([('bill_info_id', 'in', self._ids)]).read()

        records = self.env['bill.invoice.details.view'].search([('bill_info_id', 'in', self._ids)]).read()

        return {
            'template': 'bill_info_line',
            'records': records
        }

    # def get_tax_transfer(self):
    #     tax_transfer_get = self.env['account.move'].search([('id', 'in', self.account_move_id)])
    #     self.tax_transfer = tax_transfer_get.x_voucher_tax_transfer
    #
    # tax_transfer = fields.Selection('Tax Transfer', compute=get_tax_transfer)

    # その他CD
    customer_other_cd = fields.Char('Customer CD', readonly=True, compute=_get_customer_other_cd)

    bill_detail_ids = fields.One2many('bill.invoice.details', 'bill_info_id')

class ClassBillInvoice(models.Model):
    _inherit = 'bill.invoice'


class ClassDetail(models.Model):
    _inherit = 'bill.invoice.details'

    jan_code = fields.Char('Product Code', compute='_get_account_move_line_db', readonly=True)
    product_name = fields.Char('Product Code', compute='_get_account_move_line_db', readonly=True)
    product_custom_standardnumber = fields.Char('Product Custom Standard Number',
                                                compute='_get_account_move_line_db', readonly=True)
    product_default_code = fields.Char('Product Default Code', compute='_get_account_move_line_db',
                                       readonly=True)
    product_uom = fields.Char('Product Uom', compute='_get_account_move_line_db')
    # quantity = fields.Float('Product Maker Name', compute='_get_account_move_line_db', readonly=True)
    # price_unit = fields.Float(string='Unit Price', compute='_get_account_move_line_db', digits='Product Price')
    tax_audit = fields.Char('tax_audit', compute='_get_account_move_line_db', readonly=True)
    # tax_amount = fields.Float('tax_amount', compute='_get_account_move_line_db', readonly=True)
    product_maker_name = fields.Char('Product Maker Name', compute='_get_account_move_line_db', readonly=True)
    # line_amount = fields.Float('line amount', compute='_get_account_move_line_db', readonly=True)
    x_invoicelinetype = fields.Char('x_invoicelinetype', compute='_get_account_move_line_db', readonly=True)
    # voucher_line_tax_amount = fields.Float('Voucher Line Tax Amount', compute='_get_account_move_line_db')
    # tax_rate = fields.Float('tax_rate', compute='_get_account_move_line_db', readonly=True)
    flag_child_billing_code = fields.Integer('Flag Child Billing Code')

    def _get_account_move_line_db(self):
        for acc in self:
            if acc.billing_code == acc.customer_code:
                acc.flag_child_billing_code = 0
            else:
                acc.flag_child_billing_code = 1
            if acc.account_move_line_id:
                acc.jan_code = acc.account_move_line_id.product_barcode
                acc.product_name = acc.account_move_line_id.product_name
                acc.product_custom_standardnumber = acc.account_move_line_id.invoice_custom_standardnumber
                acc.product_default_code = acc.account_move_line_id.product_id.id
                acc.product_uom = acc.account_move_line_id.product_uom_id
                # acc.quantity = acc.account_move_line_id.quantity
                # acc.price_unit = acc.account_move_line_id.price_unit
                acc.tax_audit = acc.account_move_line_id.tax_audit
                # acc.tax_amount = acc.account_move_line_id.line_tax_amount
                acc.product_maker_name = acc.account_move_line_id.product_maker_name
                # acc.line_amount = acc.account_move_line_id.invoice_custom_lineamount
                acc.x_invoicelinetype = acc.account_move_line_id.x_invoicelinetype
                acc.voucher_line_tax_amount = acc.account_move_line_id.voucher_line_tax_amount
                # acc.tax_rate = acc.account_move_line_id.tax_rate
            else:
                acc.jan_code = ''
                acc.product_name = ''
                acc.product_custom_standardnumber = ''
                acc.product_default_code = ''
                acc.product_uom = ''
                # acc.quantity = False
                # acc.price_unit = False
                acc.tax_audit = ''
                # acc.tax_amount = False
                acc.product_maker_name = ''
                # acc.line_amount = False
                acc.x_invoicelinetype = ''
                # acc.tax_rate = False
                # acc.voucher_line_tax_amount = 0


class ClassDetail_View(models.Model):
    _inherit = 'bill.invoice.details'
    _name = 'bill.invoice.details.view'
    _auto = False

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW bill_invoice_details_view AS
            SELECT row_number() OVER(ORDER BY invoice_date) AS id , * FROM
            (
                SELECT
                receipt_divide_custom.name AS payment_type_name,
                account_payment_line.payment_amount,
                bill_invoice_details.bill_invoice_id,
                bill_invoice_details.bill_info_id AS bill_info_id,
                bill_invoice_details.account_move_line_id,
                bill_invoice_details.billing_code,
                bill_invoice_details.billing_name,
                bill_invoice_details.bill_no,
                bill_invoice_details.bill_date,
                bill_invoice_details.last_closing_date,
                bill_invoice_details.closing_date,
                bill_invoice_details.deadline,
                bill_invoice_details.customer_code,
                bill_invoice_details.customer_name,
                bill_invoice_details.customer_trans_classification_code,
                bill_invoice_details.active_flag,
                bill_invoice_details.hr_employee_id,
                bill_invoice_details.hr_department_id,
                bill_invoice_details.business_partner_group_custom_id,
                bill_invoice_details.customer_closing_date_id,
                bill_invoice_details.x_voucher_tax_transfer,
                bill_invoice_details.invoice_date,
                bill_invoice_details.invoice_no,
                bill_invoice_details.quantity,
                bill_invoice_details.price_unit,
                bill_invoice_details.tax_amount,
                bill_invoice_details.line_amount,
                bill_invoice_details.tax_rate,
                bill_invoice_details.voucher_line_tax_amount,
                bill_invoice_details.payment_category,
                bill_invoice_details.payment_id,
                0 as flag_child_billing_code
                FROM bill_invoice_details
                LEFT JOIN account_payment_line
                    ON bill_invoice_details.payment_id = account_payment_line.payment_id
                LEFT JOIN receipt_divide_custom
                    ON account_payment_line.receipt_divide_custom_id = receipt_divide_custom.id
                ORDER by bill_invoice_details.invoice_date
                ) AS foo
        """)

    jan_code = fields.Char('Product Code', compute='_get_account_move_line_db', readonly=True)
    product_name = fields.Char('Product Code', compute='_get_account_move_line_db', readonly=True)
    product_custom_standardnumber = fields.Char('Product Custom Standard Number',
                                                compute='_get_account_move_line_db', readonly=True)
    product_default_code = fields.Char('Product Default Code', compute='_get_account_move_line_db',
                                       readonly=True)
    product_uom = fields.Char('Product Uom', compute='_get_account_move_line_db')
    # quantity = fields.Float('Product Maker Name', compute='_get_account_move_line_db', readonly=True)
    # price_unit = fields.Float(string='Unit Price', compute='_get_account_move_line_db', digits='Product Price')
    tax_audit = fields.Char('tax_audit', compute='_get_account_move_line_db', readonly=True)
    # tax_amount = fields.Float('tax_amount', compute='_get_account_move_line_db', readonly=True)
    product_maker_name = fields.Char('Product Maker Name', compute='_get_account_move_line_db', readonly=True)
    # line_amount = fields.Float('line amount', compute='_get_account_move_line_db', readonly=True)
    x_invoicelinetype = fields.Char('x_invoicelinetype', compute='_get_account_move_line_db', readonly=True)
    # voucher_line_tax_amount = fields.Float('Voucher Line Tax Amount', compute='_get_account_move_line_db')
    tax_rate = fields.Float('tax_rate', compute='_get_account_move_line_db', readonly=True)

    bill_info_id = fields.Many2one('bill.info')
    bill_invoice_id = fields.Many2one('bill.invoice')
    account_move_line_id = fields.Many2one('account.move.line')
    payment_id = fields.Many2one('account.payment')

    billing_code = fields.Char(string='Billing Code')
    billing_name = fields.Char(string='Billing Name')
    bill_no = fields.Char(string='Bill No')
    bill_date = fields.Date(string="Bill Date")
    last_closing_date = fields.Date(string='Last Closing Date')
    closing_date = fields.Date(string='Closing Date')
    deadline = fields.Date(string='Deadline')
    customer_code = fields.Char(string='Customer Code')
    customer_name = fields.Char(string='Customer Name')
    customer_trans_classification_code = fields.Selection([('sale', 'Sale'), ('cash', 'Cash')],
                                                          string='Transaction classification', default='sale')
    active_flag = fields.Boolean(default=True)
    hr_employee_id = fields.Many2one('hr.employee', string='Customer Agent')
    hr_department_id = fields.Many2one('hr.department', string='Department')
    business_partner_group_custom_id = fields.Many2one('business.partner.group.custom', string='Supplier Group')
    customer_closing_date_id = fields.Many2one('closing.date', string='Customer Closing Date')
    x_voucher_tax_transfer = fields.Char('x_voucher_tax_transfer')
    invoice_date = fields.Date(string="Invoice Date")
    invoice_no = fields.Char(string='Invoice No')
    quantity = fields.Float('Quantity', readonly=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    tax_amount = fields.Float('tax_amount', readonly=True)
    line_amount = fields.Float('line amount', readonly=True)
    tax_rate = fields.Float('tax_rate', readonly=True)
    voucher_line_tax_amount = fields.Float('Voucher Line Tax Amount', readonly=True)
    payment_category = fields.Selection([('cash', '現金'), ('bank', '銀行')], readonly=True)

    payment_type_name = fields.Char(readonly=True)
    payment_amount = fields.Float(readonly=True)

    def _get_account_move_line_db(self):
        for acc in self:

            if not acc.payment_id:
                acc.jan_code = acc.account_move_line_id.product_barcode
                acc.product_name = acc.account_move_line_id.product_name
                acc.product_custom_standardnumber = acc.account_move_line_id.invoice_custom_standardnumber
                acc.product_default_code = acc.account_move_line_id.product_id.id
                acc.product_uom = acc.account_move_line_id.product_uom_id
                # acc.quantity = acc.account_move_line_id.quantity
                # acc.price_unit = acc.account_move_line_id.price_unit
                acc.tax_audit = acc.account_move_line_id.tax_audit
                # acc.tax_amount = acc.account_move_line_id.line_tax_amount
                acc.product_maker_name = acc.account_move_line_id.product_maker_name
                # acc.line_amount = acc.account_move_line_id.invoice_custom_lineamount
                acc.x_invoicelinetype = acc.account_move_line_id.x_invoicelinetype
                # acc.voucher_line_tax_amount = acc.account_move_line_id.voucher_line_tax_amount
                # acc.tax_rate = acc.account_move_line_id.tax_rate
            else:
                # Payment
                acc.jan_code = ''
                if acc.payment_type_name:
                    acc.product_name = '入金（' + acc.payment_type_name + '）'
                else:
                    acc.product_name = '入金'
                acc.product_custom_standardnumber = ''
                acc.product_default_code = ''
                acc.product_uom = ''
                # acc.quantity = False
                # acc.price_unit = False
                acc.tax_audit = ''
                # acc.tax_amount = False
                acc.product_maker_name = ''
                # acc.line_amount = False
                acc.x_invoicelinetype = ''
                # acc.tax_rate = 0
                # acc.voucher_line_tax_amount = 0


class ClassAccontMoveLineCustom(models.Model):
    _inherit = 'account.move.line'
    move_id = fields.Many2one('account.move', string='Account Move')

    def _get_partner_name(self):
        for par in self:
            if par.partner_id:
                par.partner_name = par.partner_id.name
            else:
                par.partner_name = ''

    partner_name = fields.Char('Partner Name', compute='_get_partner_name', readonly=True)

    def _get_product_default_code(self):
        for default in self:
            if default.product_default_code:
                default.product_default_code = default.product_id.default_code

    product_default_code = fields.Char('Product Default Code', compute='_get_product_default_code', readonly=True)

    def _get_product_custom_standerdnumber(self):
        for cus in self:
            if cus.product_custom_standardnumber:
                cus.product_custom_standardnumber = cus.product_id.product_custom_standardnumber

    product_custom_standardnumber = fields.Char('Product Custom Standard Number',
                                                compute='_get_product_custom_standerdnumber', readonly=True)

    # def _get_product_maker_name(self):
    #     for maker in self:
    #         if maker.product_maker_name:
    #             maker.product_maker_name = maker.product_id.product_maker_name

    # product_maker_name = fields.Char('Product Maker Name', compute='_get_product_maker_name', readonly=True)
