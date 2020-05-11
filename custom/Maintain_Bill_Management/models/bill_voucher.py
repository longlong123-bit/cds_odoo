from odoo import api, models, fields

class BmBillVoucher(models.Model):
    _name = 'bm.bill_voucher'

    # 品番／型番
    bill_id = fields.Many2one('bm.bill', string='Bill', required=True, readonly=True, auto_join=True,
                              help="The move of this entry line.")

    voucher_lines = fields.One2many('bm.bill_voucher_line', 'bill_voucher_id', string='Bill voucher lines',
                                       copy=True, readonly=True, Store=False)

    # Invoice for bill
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True, readonly=True, auto_join=True,
                              help="The move of this entry line.")

    invoice_date = fields.Date(readonly=True)
    invoice_no = fields.Char(readonly=True)
    customer_code = fields.Char(readonly=True)
    customer_name = fields.Char(readonly=True)