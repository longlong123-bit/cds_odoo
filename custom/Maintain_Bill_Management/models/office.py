from odoo import models, fields, api

class BmOffice(models.Model):
    _inherit = 'company.office.custom'

    # Get invoices
    def _get_invoices(self, id):
        return self.env['account.move'].search([])

    # Calculate voucher number
    def _get_voucher_number(self):
        vouchers = self._get_invoices(id=0)
        self.voucher_number = len(vouchers)

    # Voucher number
    voucher_number = fields.Integer(compute=_get_voucher_number, readonly=True, store=False)

    # Create bill when click on button [抜粋/Excerpt]
    def create_bill(self):
        # Get office
        offices = self.browse(self._ids)

        # Check if exists this office
        if offices:
            # Create bill of office
            bill = self.env['bm.bill'].create({
                'office_id': offices[0].id,
                'status': 'draft'
            })

            # Create bill detail with invoices of office
            # Get all voucher invoices
            # invoices = self.env['account.move'].search({
            #     'office_id': offices[0].id
            # })
            invoices = self._get_invoices(id = offices[0].id)

            # Create bill detail for each invoice
            for invoice in invoices:
                bill_voucher = self.env['bm.bill_voucher'].create({
                    'bill_id': bill.id,
                    'invoice_id': invoice.id,
                    'invoice_no': invoice.x_studio_document_no,
                    'invoice_date': invoice.x_studio_date_invoiced,
                    'customer_code': invoice.x_studio_business_partner.search_key_partner,
                    'customer_name': invoice.x_studio_business_partner.name
                })

                # Create voucher lines
                for line in invoice.invoice_line_ids:
                    self.env['bm.bill_voucher_line'].create({
                        'bill_voucher_id': bill_voucher.id,
                        'maker_name': '',
                        'product_code': line.product_id.product_custom_standardnumber,
                        'product_model': line.product_id.product_custom_modelnumber,
                        'product_name': line.product_id.name,
                        'quantity': line.quantity,
                        'unit_price': line.invoice_custom_priceunit,
                        'total_price': line.invoice_custom_salesunitprice,
                        'note': line.invoice_custom_Description
                    })

            # Return to detail page
            return {
                'type': 'ir.actions.act_window',
                'name': 'bm_bill_form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'bm.bill',
                'res_id': bill.id,
                'views': [(self.env.ref('Maintain_Bill_Management.bm_bill_form').id, 'form')],
                'target': 'current'
            }