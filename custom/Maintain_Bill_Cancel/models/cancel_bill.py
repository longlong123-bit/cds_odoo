from odoo import models


class BillingClass(models.Model):
    _inherit = 'bill.info'

    def cancel_bill_for_invoice(self, argsSelectedData, argsSelectedIds):
        for rec in argsSelectedData:
            bill_invoice_domain = [
                ('bill_info_id', '=', rec['id']),
            ]
            bill_invoice_details_domain = [
                ('bill_info_id', '=', rec['id']),
            ]

            bill_info_lasted_domain = [
                ('billing_code', '=', rec['billing_code']),
            ]
            bill_info_lasted = self.env['bill.info'].search(bill_info_lasted_domain,
                                                            order='deadline desc, create_date desc', limit=1)

            if rec['id'] == bill_info_lasted.id:
                bill_info_ids = self.env['bill.info'].browse(argsSelectedIds)
                bill_invoice_ids = self.env['bill.invoice'].search(bill_invoice_domain)
                bill_invoice_details_ids = self.env['bill.invoice.details'].search(bill_invoice_details_domain)

                res_partner_id = self.env["res.partner"].search(
                    ['|', ('customer_code', '=', rec['billing_code']),
                     ('customer_code_bill', '=', rec['billing_code'])])

                invoice_ids_domain = [
                    ('partner_id', 'in', res_partner_id.ids),
                    ('x_studio_date_invoiced', '<=', rec['deadline']),
                    ('state', '=', 'posted'),
                    ('type', '=', 'out_invoice'),
                    ('bill_status', '=', 'billed'),
                ]

                payment_ids_domain = [
                    ('partner_id', 'in', res_partner_id.ids),
                    ('payment_date', '<=', rec['deadline']),
                    ('state', '=', 'posted'),
                    ('bill_status', '=', 'billed'),
                ]
                if rec['last_closing_date']:
                    invoice_ids_domain += [('x_studio_date_invoiced', '>', rec['last_closing_date'])]
                    payment_ids_domain += [('payment_date', '>', rec['last_closing_date'])]

                invoice_ids = self.env['account.move'].search(invoice_ids_domain)
                payment_ids = self.env['account.payment'].search(payment_ids_domain)
                invoice_ids.write({
                    'bill_status': 'not yet'
                })
                self.env['account.move.line'].search([
                    ('id', 'in', bill_invoice_details_ids.account_move_line_id.ids)
                ]).write({
                    'bill_status': 'not yet',
                })

                payment_ids.write({
                    'bill_status': 'not yet'
                })
                payment_ids.cancel()
                payment_ids.action_draft()

                bill_info_ids.unlink()
                bill_invoice_ids.unlink()
                bill_invoice_details_ids.unlink()
            else:
                return False

        if not argsSelectedData:
            return False
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
