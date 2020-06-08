from odoo import models, fields, api


class BillHeaderClass(models.Model):
    _name = 'bill.header'

    # Customer
    partner_id = fields.Many2one('res.partner', string="Partner ID")

    # Invoice
    invoice_id = fields.Many2one('account.move', string="Invoice ID")

    # 請求先コード
    billing_code = fields.Char(string="Billing Code")
    # 請求先名（得意先名）
    billing_name = fields.Char(string="Billing Name")
    # 前回締日
    last_closing_date = fields.Date(string="Last Closing Date")
    # 締切日
    deadline = fields.Date(string="Deadline")
    # 事業部
    division = fields.Char(string="Division")
    # 営業担当者
    # sales_rep = fields.Char(string="Sales Rep", related='invoice_id.sales_rep')
    # 取引先グループ
    customer_supplier_group_code = fields.Char(string="Customer Supplier_Group_Code")

    # No
    billing_no = fields.Char(string="Billing No",
                             default=lambda self: self.env['ir.sequence'].next_by_code('001'))

    # Bill Status
    bill_status = fields.Char(string="Bill Status")
