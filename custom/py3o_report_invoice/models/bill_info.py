# -*- coding: utf-8 -*-
from odoo import models


class BillInfo(models.Model):
    _inherit = 'bill.info'

    def get_date(self):
        self.ensure_one()
        date = self.deadline.strftime('%Y年 %m月 %d日')
        return date


class BillInvoiceDetail(models.Model):
    _inherit = 'bill.invoice.details'

    def _format_invoice_date(self):
        self.ensure_one()
        date = self.invoice_date.strftime('%y/%m/%d')
        return date

    def format_tax_title(self):
        self.ensure_one()
        if (self.x_voucher_tax_transfer == 'foreign_tax') or (self.x_voucher_tax_transfer == 'voucher'):
            tax_title = '税転嫁'
        else:
            tax_title = ''
        return tax_title
