from odoo import models, fields, api

class BmBillVoucherLine(models.Model):
    _name = 'bm.bill_voucher_line'

    bill_voucher_id = fields.Many2one('bm.bill_voucher', string='Bill vouchers', required=True, readonly=True, auto_join=True,
                              help="The move of this entry line.")
    marker_name = fields.Char(readonly=True)
    product_code = fields.Char(readonly=True)
    product_model = fields.Char(readonly=True)
    product_name = fields.Char(readonly=True)
    quantity = fields.Integer(readonly=True)
    unit_price = fields.Float(readonly=True)
    total_price = fields.Float(readonly=True)
    note = fields.Char(readonly=True)