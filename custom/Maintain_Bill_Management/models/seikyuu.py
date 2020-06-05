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
            ('state', '=', 'posted'),
            ('type', '=', 'out_invoice'),
            ('is_seikyuu_created', '=', False),
        ])

    def _compute_voucher_number(self, record):
        # Temporary variables are used to calculate voucher number
        number = 0

        # Get the records in the "res_partner" table with the same "請求先" as seikyuu_code
        res_partner_id = self.env["res.partner"].search(
            ['|', ('customer_code', '=', record.customer_code), ('customer_code_bill', '=', record.customer_code)])

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

    # 前回締日
    last_closing_date = fields.Date(compute=_set_data_to_fields, readonly=True, store=False)

    # 締切日
    deadline = fields.Date(compute=_set_data_to_fields, readonly=True, store=False)

    # Voucher Number
    voucher_number = fields.Integer(compute=_set_data_to_fields, readonly=True, store=False)

    # Check customer is Seikyuu Place
    is_seikyuu_place = fields.Boolean(default=False)

    # Relational fields with account.move model
    account_move_ids = fields.One2many('account.move', 'seikyuu_place_id', string='Invoices')

    # Button [抜粋/Excerpt]
    def bm_seikyuu_excerpt_button(self):

        res_partner_id = self.env["res.partner"].search(
            ['|', ('customer_code', '=', self.customer_code), ('customer_code_bill', '=', self.customer_code)])

        self.account_move_ids = self._get_invoices_by_partner_id(partner_id=res_partner_id.ids,
                                                                 last_closing_date=self.last_closing_date,
                                                                 deadline=self.deadline)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Seikyuu Details',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'res_id': self.id,
            'views': [(self.env.ref('Maintain_Bill_Management.bm_seikyuu_form').id, 'form')],
        }

    # Action
    def action_seikyuu(self):
        print(self.ids)
        print(self.ids)
        print(self.ids)
        print(self.ids)
        return True

    # Test button
    def test_buttonCC(self):
        print(self.customer_code_bill)
        return True

    def get_lines(self):
        records = self.env['account.move.line'].search([
            ('move_id', 'in', self._ids),
            ('product_id', '!=', False)
        ]).read()

        # Get tax
        for record in records:
            if record['tax_ids']:
                self._cr.execute('''
                                            SELECT id, name
                                            FROM account_tax
                                            WHERE id IN %s
                                        ''', [tuple(record['tax_ids'])])
                query_res = self._cr.fetchall()
                record['tax_ids'] = ', '.join([str(res[1]) for res in query_res])

        return {
            'template': 'seikyuu.product_lines',
            'records': records
        }


class InvoiceClass(models.Model):
    _inherit = 'account.move'

    is_seikyuu_created = fields.Boolean()

    seikyuu_place_id = fields.Many2one('res.partner')
