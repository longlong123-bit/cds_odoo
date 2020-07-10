# -*- coding: utf-8 -*-
from odoo import models


class BillInfo(models.Model):
    _inherit = 'bill.info'

    def get_date(self):
        self.ensure_one()
        date = self.date.strftime('%Y年　%m月 %d日')
        return date
