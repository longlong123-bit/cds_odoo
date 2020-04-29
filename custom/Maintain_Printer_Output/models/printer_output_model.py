# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ClassPrinterOutput(models.Model):
    _name = 'printer.output'

    computer_name = fields.Char('Computer Name')
    paperformat_id_1 = fields.Many2one('report.paperformat', 'Paper Format')
    paperformat_id_2 = fields.Many2one('report.paperformat', 'Paper Format 1')
    paperformat_id_3 = fields.Many2one('report.paperformat', 'Paper Format 2')
    paperformat_id_4 = fields.Many2one('report.paperformat', 'Paper Format 3')


