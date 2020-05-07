from odoo import models, fields

class BillDetail(models.Model):
    _name = 'bm.bill_detail'

    #bill_id = fields.Integer()

    # # 伝票No
    # slip_number = fields.Char()
    #
    # 得意先コード
    customer_code = fields.Char()

    # 得意先名
    customer_name = fields.Char()
    #
    # # メーカー名
    # manufacture_name = fields.Char()

    # 品番／型番
    bill_id = fields.Many2one('bm.bill', string='Bill', index=True, required=True, readonly=True, auto_join=True,
                              help="The move of this entry line.")

    # Invoice for bill
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True, readonly=True, auto_join=True,
                              help="The move of this entry line.")