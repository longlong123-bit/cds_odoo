# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_date(self):
        self.ensure_one()
        date = self.date.strftime('%Y年　%m月 %d日')
        print("====== date: ", date, type(date))
        return date
