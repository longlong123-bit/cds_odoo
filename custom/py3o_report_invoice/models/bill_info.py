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
