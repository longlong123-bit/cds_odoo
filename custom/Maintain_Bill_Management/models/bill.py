from odoo import models, fields, api

class BmBill(models.Model):
    _name = 'bm.bill'

    # Get information of office
    def _get_office_code(self):
        if self.office_id:
            self.office_code = self.office_id.office_code

    # Get information of office
    def _get_office_name(self):
        if self.office_id:
            self.office_name = self.office_id.name

    # Get information of office
    def _get_office_closing_date(self):
        if self.office_id:
            self.office_closing_date = self.office_id.office_closing_date

    # Get invoices for billing
    bill_vouchers = fields.One2many('bm.bill_voucher', 'bill_id', string='Bill vouchers',
                                       copy=True, readonly=True, Store=False)

    # Status of bill
    status = fields.Char()

    # Office of bill
    office_id = fields.Many2one('company.office.custom', string='Office', required=True, readonly=True, auto_join=True,
                              help="The move of this entry line.")

    office_code = fields.Char(compute=_get_office_code, readonly=True, store=False)
    office_name = fields.Char(compute=_get_office_name, readonly=True, store=False)
    office_closing_date = fields.Date(compute=_get_office_closing_date, readonly=True, store=False)