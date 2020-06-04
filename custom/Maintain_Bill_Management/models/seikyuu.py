from odoo import models, fields, api
from datetime import date, timedelta
import calendar


class SeiKyuuClass(models.Model):
    _inherit = 'res.partner'

    @staticmethod
    def _compute_closing_date(customer_closing_date):
        today = date.today()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        if today.month != 1:
            days_in_last_month = calendar.monthrange(today.year, today.month - 1)[1]
        else:
            days_in_last_month = calendar.monthrange(today.year - 1, 12)[1]
        _start = customer_closing_date.start_day
        _circle = customer_closing_date.closing_date_circle

        # if _start <= today.day:
        #     _current_closing_date = today.replace(day=days_in_month)
        #     _last_closing_date = _current_closing_date.replace(day=_start) - timedelta(days=1)
        #     if (_start + _circle) <= days_in_month:
        #         while today.day >= (_start + _circle):
        #             _start = _start + _circle
        #         if (_start + _circle) > days_in_month:
        #             _current_closing_date = _current_closing_date.replace(day=days_in_month)
        #             _last_closing_date = _current_closing_date.replace(day=_start) - timedelta(days=1)
        #         else:
        #             _current_closing_date = _current_closing_date.replace(day=_start + _circle - 1)
        #             _last_closing_date = _current_closing_date - timedelta(days=_circle)
        # else:
        #     _current_closing_date = today.replace(day=_start) - timedelta(days=1)
        #     _last_closing_date = today.replace(day=days_in_month) - timedelta(days=days_in_month)

        if today.day < _start:
            _current_closing_date = today.replace(day=_start) - timedelta(days=1)
            _last_closing_date = _current_closing_date - timedelta(days=days_in_last_month)
        else:
            _last_closing_date = today.replace(day=_start) - timedelta(days=1)
            _current_closing_date = _last_closing_date + timedelta(days=days_in_month)

        closing_date = {
            'last_closing_date': _last_closing_date,
            'current_closing_date': _current_closing_date,
        }

        return closing_date

    # Get invoices list by partner id
    def _get_invoices_by_partner_id(self, partner_id, last_closing_date, deadline):
        return self.env['account.move'].search([
            ('partner_id', 'in', partner_id),
            ('x_studio_date_invoiced', '>', last_closing_date),
            ('x_studio_date_invoiced', '<=', deadline),
            ('is_seikyuu_created', '=', False),
            ('state', '=', 'posted'),
        ])

    def _compute_voucher_number(self, record):
        # Temporary variables are used to calculate voucher number
        number = 0

        # Get the records in the "res_partner" table with the same "請求先" as seikyuu_code
        res_partner_id = self.env["res.partner"].search(
            ['|', ('id', '=', record.id), ('parent_id', '=', record.id)])

        # Calculate voucher number
        for rec in res_partner_id:
            number = number + len(self._get_invoices_by_partner_id(partner_id=rec.ids,
                                                                   last_closing_date=record.last_closing_date,
                                                                   deadline=record.deadline))
        return number

    @api.depends('customer_code', 'customer_code_bill')
    def _set_data_to_fields(self):
        for record in self:

            # Set data for last_closing_date field and deadline field
            if record.customer_closing_date:
                _closing_date = self._compute_closing_date(customer_closing_date=record.customer_closing_date)
                record.last_closing_date = _closing_date['last_closing_date']
                record.deadline = _closing_date['current_closing_date']

            # Set data for voucher_number field
            record.voucher_number = self._compute_voucher_number(record=record)

        return True

    @api.constrains('customer_code', 'customer_code_bill')
    def _check_seikyuu_place(self):
        for record in self:
            # Customer has customer_code equal with customer_code_bill. This is a Seikyuu Place
            if record.customer_code == record.customer_code_bill:
                record.is_seikyuu_place = True
            else:
                record.is_seikyuu_place = False

    # Last Closing Date
    last_closing_date = fields.Date(compute=_set_data_to_fields, readonly=True, store=False)

    # Deadline
    deadline = fields.Date(compute=_set_data_to_fields, readonly=True, store=False)

    # Voucher Number
    voucher_number = fields.Integer(compute=_set_data_to_fields, readonly=True, store=False)

    # Check customer is Seikyuu Place
    is_seikyuu_place = fields.Boolean(default=False)

    # Seikyuu Details ID
    seikyuu_details_id = fields.One2many('seikyuu.details', 'seikyuu_id', string="Seikyuu Details ID", index=True,
                                         auto_join=True, help="The move of this entry line.")

    # Create record
    def _create_seikyuu_details(self, seikyuu, status):
        # Create data seikyuu details of seikyuu place
        seikyuu_details = self.env['seikyuu.details'].create({
            'seikyuu_id': seikyuu.id,
            'status': status
        })

        # Get the records in the "res_partner" table with the same "請求先" as seikyuu_code
        res_partner_id = self.env["res.partner"].search(
            ['|', ('id', '=', seikyuu.id), ('parent_id', '=', seikyuu.id)])

        # Get closing date
        if seikyuu.customer_closing_date:
            _closing_date = self._compute_closing_date(customer_closing_date=seikyuu.customer_closing_date)
            last_closing_date = _closing_date['last_closing_date']
            deadline = _closing_date['current_closing_date']

        # Get invoices of seikyuu place
        invoices = self._get_invoices_by_partner_id(partner_id=res_partner_id.ids,
                                                    last_closing_date=last_closing_date,
                                                    deadline=deadline)

        # For each invoice, create a seikyuu details line
        for invoice in invoices:
            # create a seikyuu details line
            seikyuu_details_line = self.env['seikyuu.details.line'].create({
                'seikyuu_details_id': seikyuu_details.id,
                'invoice_id': invoice.id,
            })

        return seikyuu_details

    def _get_seikyuu_details(self, seikyuu, status):
        # Get seikyuu details of seikyuu place
        seikyuu_details = self.env['seikyuu.details'].search([('seikyuu_id', '=', seikyuu.id), ('status', '=', status)])

        # Get seikyuu details line
        seikyuu_details_line = self.env['seikyuu.details.line'].search(
            [('seikyuu_details_id', '=', seikyuu_details.id)])

        return seikyuu_details

    # Button [抜粋/Excerpt]
    def bm_seikyuu_excerpt_button(self):
        for seikyuu in self:
            _closing_date = self._compute_closing_date(customer_closing_date=seikyuu.customer_closing_date)
            if seikyuu.id in self.env['seikyuu.details'].search([]).seikyuu_id.ids:
                seikyuu_details = self._get_seikyuu_details(seikyuu=seikyuu, status='draft')
            else:
                seikyuu_details = self._create_seikyuu_details(seikyuu=seikyuu, status='draft')

        ctx = self._context.copy()
        ctx['last_closing_date'] = self.last_closing_date
        ctx['deadline'] = self.deadline

        return {
            'type': 'ir.actions.act_window',
            'name': 'Seikyuu Details',
            'view_mode': 'form',
            'res_model': 'seikyuu.details',
            'res_id': seikyuu_details.id,
            'views': [(self.env.ref('Maintain_Bill_Management.bm_seikyuu_details_form').id, 'form')],
            'context': ctx
        }

    # Action
    def action_seikyuu(self):
        print(self.ids)
        print(self.ids)
        print(self.ids)
        print(self.ids)
        return True


class InvoiceClass(models.Model):
    _inherit = 'account.move'

    is_seikyuu_created = fields.Boolean()
