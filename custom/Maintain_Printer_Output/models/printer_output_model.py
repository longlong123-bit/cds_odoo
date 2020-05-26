# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ClassPrinterOutput(models.Model):
    _name = 'printer.output'

    computer_name = fields.Char('Computer Name')
    paperformat_id_1 = fields.Selection([('all', 'All'),('quotation', 'Quotation'),('voucher', 'Voucher'),('invoice','Invoice'),('report','Report')], 'Paper Format 1')
    paperformat_id_2 = fields.Selection([('all', 'All'),('quotation', 'Quotation'),('voucher', 'Voucher'),('invoice','Invoice'),('report','Report')], 'Paper Format 2')
    paperformat_id_3 = fields.Selection([('all', 'All'),('quotation', 'Quotation'),('voucher', 'Voucher'),('invoice','Invoice'),('report','Report')], 'Paper Format 3')
    paperformat_id_4 = fields.Selection([('all', 'All'),('quotation', 'Quotation'),('voucher', 'Voucher'),('invoice','Invoice'),('report','Report')], 'Paper Format 4')
    printer_output_1 = fields.Selection([('printer1', 'Printer 1'),('printer2', 'Printer 2'),('printer3','Printer 3'),('printer4','Printer 4')],'Printer Output 1')
    printer_output_2 = fields.Selection(
        [('printer1', 'Printer 1'), ('printer2', 'Printer 2'), ('printer3', 'Printer 3'), ('printer4', 'Printer 4')],
        'Printer Output 2')
    printer_output_3 = fields.Selection(
        [('printer1', 'Printer 1'), ('printer2', 'Printer 2'), ('printer3', 'Printer 3'), ('printer4', 'Printer 4')],
        'Printer Output 3')
    printer_output_4 = fields.Selection(
        [('printer1', 'Printer 1'), ('printer2', 'Printer 2'), ('printer3', 'Printer 3'), ('printer4', 'Printer 4')],
        'Printer Output 4')
    active = fields.Boolean('Active', default=True)


