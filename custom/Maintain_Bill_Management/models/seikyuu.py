from odoo import models, fields, api


class SeiKyuuClass(models.Model):
    _inherit = 'res.partner'

    def _get_invoices_by_partner_id(self, partner_id, last_closing_date, deadline):
        return self.env['account.move'].search([
            ('partner_id', 'in', partner_id),
            ('x_studio_date_invoiced', '>', last_closing_date),
            ('x_studio_date_invoiced', '<=', deadline),
            ('is_billed', '=', False)
        ])

    def _compute_voucher_number(self):
        for record in self:
            # Temporary variables are used to calculate voucher number
            number = 0

            # Get the records in the "res_partner" table with the same "請求先" as seikyuu_code
            res_partner_id = self.env["res.partner"].search(
                ['|', ('id', '=', record.id), ('parent_id', '=', record.id)])

            # Calculate voucher number
            for rec in res_partner_id:
                number = number + len(self._get_invoices_by_partner_id(partner_id=rec.ids,
                                                                       last_closing_date='2020-04-30',
                                                                       deadline='2020-05-30'))

            # Set value of the number to a voucher_number field
            record.voucher_number = number
        return True

    # Voucher number
    voucher_number = fields.Integer(compute=_compute_voucher_number, readonly=True, store=False)

    # Seikyuu Details ID
    seikyuu_details_id = fields.One2many('seikyuu.details', 'seikyuu_id', string="Seikyuu Details ID", index=True,
                                         auto_join=True, help="The move of this entry line.")

    # Create record
    def _create(self, seikyuu, status):
        # Create data seikyuu details of seikyuu place
        seikyuu_details = self.env['seikyuu.details'].create({
            'seikyuu_id': seikyuu.id,
            'status': status
        })

        res_partner_id = self.env["res.partner"].search(
            ['|', ('id', '=', seikyuu.id), ('parent_id', '=', seikyuu.id)])

        print(res_partner_id)

        # Get invoices of seikyuu place
        invoices = self._get_invoices_by_partner_id(partner_id=res_partner_id.ids,
                                                    last_closing_date='2020-04-30',
                                                    deadline='2020-05-30')

        # For each invoice, create a seikyuu details line
        for invoice in invoices:
            print("invoice => ", invoice)
            # create a seikyuu details line
            seikyuu_details_line = self.env['seikyuu.details.line'].create({
                'seikyuu_details_id': seikyuu_details.id,
                'invoice_id': invoice.id,
            })

        return seikyuu_details

    def _get(self, seikyuu, status):
        # Get seikyuu details of seikyuu place
        seikyuu_details = self.env['seikyuu.details'].search([('seikyuu_id', '=', seikyuu.id), ('status', '=', status)])

        # Get seikyuu details line
        seikyuu_details_line = self.env['seikyuu.details.line'].search(
            [('seikyuu_details_id', '=', seikyuu_details.id)])

        return seikyuu_details

    # Create/Update draft seikyuu
    def create_update_draft_seikyuu(self):
        for seikyuu in self:
            seikyuu_details = self._create(seikyuu=seikyuu, status='draft')
        return seikyuu_details

    # Button [抜粋/Excerpt]
    def bm_seikyuu_excerpt_button(self):
        for seikyuu in self:
            if seikyuu.id in self.env['seikyuu.details'].search([]).seikyuu_id.ids:
                seikyuu_details = self._get(seikyuu=seikyuu, status='draft')
            else:
                seikyuu_details = self._create(seikyuu=seikyuu, status='draft')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Seikyuu Details',
            'view_mode': 'form',
            'res_model': 'seikyuu.details',
            'res_id': seikyuu_details.id,
            'views': [(self.env.ref('Maintain_Bill_Management.bm_seikyuu_details_form').id, 'form')],
        }

    # Action
    def action_seikyuu(self):
        print(self.ids)
        print(self.ids)
        print(self.ids)
        print(self.ids)
        return True
