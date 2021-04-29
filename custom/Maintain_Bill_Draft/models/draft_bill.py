from odoo import models, _, api
from odoo.exceptions import UserError


class DraftBillingClass(models.Model):
    _inherit = 'bill.info.draft'

    def draft_bill_for_invoice(self, argsSelectedData, argsSelectedIds):
        for rec in argsSelectedData:
            bill_invoice_domain = [
                ('bill_info_id', '=', rec['id']),
            ]
            bill_invoice_details_domain = [
                ('bill_info_id', '=', rec['id']),
            ]

            bill_info_lasted_domain = [
                ('billing_code', '=', rec['billing_code'])
            ]
            bill_info_lasted = self.env['bill.info.draft'].search(bill_info_lasted_domain,
                                                            order='deadline desc, create_date desc', limit=1)

            if rec['id'] == bill_info_lasted.id:
                bill_info_ids = self.env['bill.info.draft'].browse(rec['id'])
                bill_invoice_ids = self.env['bill.invoice.draft'].search(bill_invoice_domain)
                bill_invoice_details_ids = self.env['bill.invoice.details.draft'].search(bill_invoice_details_domain)

                invoice_ids_domain = [
                    ('id', 'in', bill_invoice_ids.account_move_id.ids)
                ]

                payment_ids_domain = [
                    ('id', 'in', bill_invoice_details_ids.payment_id.ids)
                ]

                invoice_ids = self.env['account.move'].search(invoice_ids_domain)
                payment_ids = self.env['account.payment'].search(payment_ids_domain)

                invoice_ids.write({
                    'bill_status': 'not yet',
                })

                bill_invoice_details_ids.account_move_line_id.write({
                    'bill_status': 'not yet',
                })

                payment_ids.write({
                    'bill_status': 'not yet',
                })
                payment_ids.filtered(lambda l: l.state == 'posted').cancel()
                payment_ids.filtered(lambda l: l.state == 'cancelled').action_draft()

                bill_info_ids.unlink()
                bill_invoice_ids.unlink()
                bill_invoice_details_ids.unlink()
            else:
                raise UserError(_("You can only cancel a billing process that has the latest deadline."))
                return False

        if not argsSelectedData:
            return False
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context.copy()
        if ctx.get('have_advance_search'):
            domain = []
            if 'Draft Bill History' == ctx.get('view_name'):
                for se in args:
                    if se[0] == '&':
                        continue
                    if 'customer_closing_date_id' == se[0]:
                        if se[2].isnumeric():
                            se[0] = 'customer_closing_date_id.start_day'
                            se[1] = '='
                    if 'customer_excerpt_request' == se[0]:
                        if se[2] == 'True':
                            se[2] = True
                            # domain += [se]
                        elif se[2] == 'False':
                            se[2] = False
                        else:
                            continue
                    domain += [se]
                args = domain
        if 'Draft Bill History' == ctx.get('view_name') and len(args) == 0:
            return []

        return super(DraftBillingClass, self).search(args, offset=offset, limit=limit, order=order, count=count)