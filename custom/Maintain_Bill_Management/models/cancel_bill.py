from odoo import models, fields, api


class CancelBillClass(models.Model):
    _inherit = 'bill.header'

    def testButton(self):
        print(self.partner_id.name)
        print(self.invoice_id.sales_rep)
        return True

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
