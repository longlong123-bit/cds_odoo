# -*- coding: utf-8 -*-
from odoo import fields, models


class ClassReportConstantMaster(models.Model):
    _name = 'report.constant.master'

    company_id = fields.Many2one('res.company', required=True)
    report_type = fields.Selection(
        [('re_type_quotation_001', '見積票　ー　通常'),
         ('re_type_quotation_002', '見積票　ー　神栖営業所用'),
         ('re_type_quotation_003', '見積票　ー　鹿島見積'),
         ('re_type_delivery_001', '納品票　ー　通常'),
         ('re_type_delivery_002', '納品票　ー　ヤマサタイプ'),
         ('re_type_delivery_003', '納品票　ー　岡田土建タイプ'),
         ('re_type_delivery_004', '納品票　ー　銚子信用金庫'),
         ('re_type_sale_001', '売上伝票'),
         ('re_type_sale_002', '売上伝票　ー　確認伝票'),
         ('re_type_bill_001', '請求書　ー　通常請求書'),
         ('re_type_bill_002', '請求書　ー　ヤマサ請求'),
         ('re_type_bill_003', '請求書　ー　適用付請求'),
         ('re_type_bill_004', '請求書　ー　当月請求書'),
         ('re_type_bill_005', '請求書　ー　通常請求書(得意先毎)'),
         ('re_type_bill_006', '請求書　ー　預り請求書'),
         ('re_type_bill_007', '請求書　ー　預り請求書１')], required=True, default='re_type_quotation_001')
    apply_date = fields.Date('apply_date', required=True)
    representative = fields.Char(required=True)
    remarks = fields.Char('remarks', size=200)


