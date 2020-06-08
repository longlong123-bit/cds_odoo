from odoo import models, fields, api


class BillHeaderClass(models.Model):
    _name = 'bill.header'

    billing_code = fields.Char(string="Billing Code")
    billing_name = fields.Char(string="Billing Name")
    last_closing_date = fields.Date(string="Last Closing Date")
    deadline = fields.Date(string="Deadline")
    billing_no = fields.Char(string="Billing No",
                             default=lambda self: self.env['ir.sequence'].next_by_code('001'))
    # Invoice
    invoice_id = fields.Many2one('account.move', string="Invoice ID")

    bill_status = fields.Char(string="Bill Status")

    def cancel_bill_for_invoice(self, argsSelectedData, argsSelectedIds):
        for rec in argsSelectedData:
            invoice_ids = self.env['account.move'].search([
                ('id', '=', rec['invoice_id']['data']['id']),
            ])
            invoice_ids.write({
                'bill_status': 'not yet'
            })

        self.search([('id', 'in', argsSelectedIds)]).unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
