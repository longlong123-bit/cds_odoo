from odoo import models, fields, api


class BillingClass(models.Model):
    _inherit = 'bill.info'

    def cancel_bill_for_invoice(self, argsSelectedData, argsSelectedIds):
        for rec in argsSelectedData:
            res_partner_id = self.env["res.partner"].search(
                ['|', ('customer_code', '=', rec['billing_code']), ('customer_code_bill', '=', rec['billing_code'])])

            invoice_ids = self.env['account.move'].search([
                ('partner_id', 'in', res_partner_id.ids),
                ('x_studio_date_invoiced', '>', rec['last_closing_date']),
                ('x_studio_date_invoiced', '<=', rec['closing_date']),
                ('state', '=', 'posted'),
                ('type', '=', 'out_invoice'),
                ('bill_status', '=', 'billed'),
            ])

            invoice_ids.write({
                'bill_status': 'not yet'
            })
            self.env['account.move.line'].search([('move_id', 'in', invoice_ids.ids)]).write({
                'bill_status': 'not yet',
                'selected': False
            })

            self.env['bill.info'].search([('id', 'in', argsSelectedIds)]).unlink()

            self.env['bill.invoice'].search([
                ('billing_code', '=', rec['billing_code']),
                ('bill_date', '=', rec['bill_date']),
                ('last_closing_date', '=', rec['last_closing_date']),
            ]).unlink()

            self.env['bill.invoice.details'].search([
                ('billing_code', '=', rec['billing_code']),
                ('bill_date', '=', rec['bill_date']),
                ('last_closing_date', '=', rec['last_closing_date']),
            ]).unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context.copy()
        if 'Cancel Billing' == ctx.get('view_name'):
            for record in args:
                if 'customer_excerpt_request' == record[0]:
                    if record[2] == 'True':
                        record[2] = True
                    else:
                        record[2] = False

        res = self._search(args, offset=offset, limit=limit, order=order, count=count)
        return res if count else self.browse(res)
