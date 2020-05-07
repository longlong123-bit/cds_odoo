from odoo import models, fields, api

class Bill(models.Model):
    _name = 'bm.bill'

    # 締日（締日グループ）
    # master ngày kết sổ
    # Todo dợi màn hình của anh Minh
    closing_date = fields.Date()

    # Customer
    customer = fields.Many2one('res.partner')

    # 抜粋請求区分
    request_category = fields.Boolean(default=False)

    # 締切日
    deadline = fields.Date()

    # 事業部
    division = fields.Date()

    # 営業担当者
    sale_representative = fields.Char()

    # 取引先グループ
    supplier_group = fields.Char()

    # 請求先
    bill_address = fields.Char()

    # 請求先コード
    bill_code = fields.Char()

    # 請求先名（得意先名）
    bill_party_name = fields.Char()

    # 前回締日
    # last_close_date = fields.Date()

    # 売伝枚数
    sale_number = fields.Char()

    # 売上日付
    sale_date = fields.Date()

    # Get invoices for billing
    bill_detail = fields.One2many('bm.bill_detail','bill_id', string='Bill detail',
                                       copy=True, readonly=True)
