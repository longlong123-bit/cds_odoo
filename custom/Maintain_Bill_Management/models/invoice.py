from odoo import models, fields, api

class BillInvoice(models.Model):
    _inherit = 'account.move'

    def create_bill(self):
        # Get all invoices
        invoices = self.browse(self._ids)

        # Create bill
        bill = self.env['bm.bill'].create({
            'bill_code': 123,
            'bill_address': '123',
            'bill_party_name': 'bill name'
        })

        # Create bill detail
        for invoice in invoices:
            self.env['bm.bill_detail'].create({
                'bill_id': bill.id,
                'invoice_id': invoice.id
            })

        # Return to bill detail
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintain_Bill_Management.bm.bill.form',
            'res_model': 'bm.bill',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(bill.id, 'tree'), (False, 'form')],
            'view_id ref="Maintain_Bill_Management.bm_bill_form"': '',
            'target': 'current',
            #'domain': domain,
        }