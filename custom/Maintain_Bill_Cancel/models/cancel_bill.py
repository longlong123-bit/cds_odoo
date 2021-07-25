from odoo import models, _
from odoo.exceptions import UserError

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
                ('billing_code', '=', rec['billing_code'])
            ]
            bill_info_lasted = self.env['bill.info'].search(bill_info_lasted_domain,
                                                            order='deadline desc, create_date desc', limit=1)

            if rec['id'] == bill_info_lasted.id:
                bill_info_ids = self.env['bill.info'].browse(rec['id'])
                bill_invoice_ids = self.env['bill.invoice'].search(bill_invoice_domain)
                bill_invoice_details_ids = self.env['bill.invoice.details'].search(bill_invoice_details_domain)

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
                # raise UserError(_("You can only cancel a billing process that has the latest deadline."))
                return False

        if not argsSelectedData:
            return False
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def search(self, args, offset=0, limit=None, order=None, count=False):
        module_context = self._context.copy()
        if module_context.get('have_advance_search') and module_context.get('bill_management_module'):
            domain = []
            billing_ids = []
            billing_query = []
            for record in args:
                if 'billing_code' in record:
                    billing_query.append("LOWER(billing_code) {0} '{1}'".format(record[1], record[2].lower()))
                else:
                    domain += [record]
                    # billing_query.append("{0} {1} '{2}'".format(record[0], record[1], record[2]))

            if billing_query:
                query = 'SELECT id FROM bill_info WHERE ' + ' AND '.join(billing_query)
                self._cr.execute(query)
                query_res = self._cr.dictfetchall()
                for bill_record in query_res:
                    billing_ids.append(bill_record.get('id'))
                domain += [['id', 'in', billing_ids]]
            args = domain
        res = super(BillingClass, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res
