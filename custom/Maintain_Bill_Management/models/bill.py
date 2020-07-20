import datetime

from odoo import models, fields, api
from datetime import datetime, date, timedelta
import math
from ...Maintain_Accounts_Receivable_Balance_List.models import accounts_receivable_balance_list as advanced_search


class BillingClass(models.Model):
    _inherit = 'res.partner'

    def _compute_closing_date_for_bill(self, record):
        _last_closing_date = ''
        _deadline = date.today()
        if advanced_search.val_bill_search_deadline:
            _deadline = datetime.strptime(advanced_search.val_bill_search_deadline, '%Y-%m-%d').date()

        res_partner_ids = self.env["res.partner"].search(
            ['|', ('customer_code', '=', record.customer_code), ('customer_code_bill', '=', record.customer_code)])

        last_data_bill_info_ids = self.env['bill.info'].search([
            ('partner_id', 'in', res_partner_ids.ids),
            # ('closing_date', '<=', _deadline),
        ], order='deadline desc', limit=1)

        if last_data_bill_info_ids:
            _last_closing_date = last_data_bill_info_ids.deadline

        if _last_closing_date:
            invoice_line_ids = self.env['account.move.line'].search([
                ('partner_id', 'in', res_partner_ids.ids),
                ('date', '<=', _last_closing_date),
                ('bill_status', '=', 'not yet'),
                ('account_internal_type', '=', 'other'),
                ('parent_state', '=', 'posted'),
            ])

            if len(invoice_line_ids) != 0:
                _last_closing_date = last_data_bill_info_ids.last_closing_date

        closing_date = {
            'last_closing_date': _last_closing_date,
            'deadline': _deadline,
        }

        return closing_date

    # Get invoices list by partner id
    def _get_invoices_by_partner_id(
            self, partner_id, last_closing_date, deadline):
        domain = [('partner_id', 'in', partner_id),
                  ('x_studio_date_invoiced', '<=', deadline),
                  ('state', '=', 'posted'),
                  ('type', '=', 'out_invoice'),
                  ('bill_status', '!=', 'billed')]
        if last_closing_date:
            domain += [('x_studio_date_invoiced', '>', last_closing_date)]
        out_invoices = self.env['account.move'].search(domain)
        return out_invoices

    def _get_invoices_sales_by_partner_id(self, partner_id, last_closing_date, deadline):
        if last_closing_date:
            return self.env['account.move'].search([
                ('partner_id', 'in', partner_id),
                ('x_studio_date_invoiced', '>', last_closing_date),
                ('x_studio_date_invoiced', '<=', deadline),
                ('state', '=', 'posted'),
                ('type', '=', 'out_invoice'),
                ('bill_status', '!=', 'billed'),
                ('customer_trans_classification_code', '!=', 'cash'),
            ])
        else:
            return self.env['account.move'].search([
                ('partner_id', 'in', partner_id),
                ('x_studio_date_invoiced', '<=', deadline),
                ('state', '=', 'posted'),
                ('type', '=', 'out_invoice'),
                ('bill_status', '!=', 'billed'),
                ('customer_trans_classification_code', '!=', 'cash'),
            ])

    def _compute_voucher_number(self, record):
        # Temporary variables are used to calculate voucher number
        number = 0

        # Get the records in the "res_partner" table with the same "請求先" as billing_code
        res_partner_id = self.env["res.partner"].search(
            ['|', ('customer_code', '=', record.customer_code), ('customer_code_bill', '=', record.customer_code)])

        # Calculate voucher number
        for rec in res_partner_id:
            number = number + len(self._get_invoices_sales_by_partner_id(partner_id=rec.ids,
                                                                         last_closing_date=record.last_closing_date,
                                                                         deadline=record.deadline))
        return number

    def _set_data_to_fields(self):
        for record in self:
            _last_billed_amount = 0
            _deposit_amount = 0
            _balance_amount = 0
            _amount_untaxed = 0
            _tax_amount = 0
            _amount_total = 0
            _billed_amount = 0
            # Set data for last_closing_date field and deadline field
            if record.customer_closing_date:
                _closing_date = self._compute_closing_date_for_bill(record=record)
                record.last_closing_date = _closing_date['last_closing_date']
                record.deadline = _closing_date['deadline']

            # Set data for voucher_number field
            record.voucher_number = self._compute_voucher_number(record=record)

            # Set data for department field
            record.department = record.customer_agent.department_id.id

            # Compute data for last_billed_amount field
            bill_info_ids = self.env['bill.info'].search([('billing_code', '=', record.customer_code),
                                                          ('deadline', '<=', record.last_closing_date),
                                                          ('active_flag', '=', True)],
                                                         order="deadline desc, bill_no desc", limit=1)

            for bill in bill_info_ids:
                _last_billed_amount = bill.billed_amount

            # Compute data for deposit_amount field
            if record.last_closing_date:
                payment_ids = self.env['account.payment'].search([
                    ('partner_id', 'in', record.ids),
                    ('payment_date', '>', record.last_closing_date),
                    ('payment_date', '<=', record.deadline),
                    ('state', '=', 'posted'),
                    ('bill_status', '!=', 'billed'),
                ])
            else:
                payment_ids = self.env['account.payment'].search([
                    ('partner_id', 'in', record.ids),
                    ('payment_date', '<=', record.deadline),
                    ('state', '=', 'posted'),
                    ('bill_status', '!=', 'billed'),
                ])

            for payment_id in payment_ids:
                if payment_id.payment_amount:
                    _deposit_amount = _deposit_amount + payment_id.payment_amount

            # Compute data for balance_amount field
            _balance_amount = _last_billed_amount - _deposit_amount

            # Compute data for amount_untaxed, tax_amount, billed_amount fields
            res_partner_id = self.env["res.partner"].search(
                ['|', ('customer_code', '=', record.customer_code), ('customer_code_bill', '=', record.customer_code)])

            if record.last_closing_date:
                invoice_ids = self.env['account.move'].search([
                    ('partner_id', 'in', res_partner_id.ids),
                    ('x_studio_date_invoiced', '>', record.last_closing_date),
                    ('x_studio_date_invoiced', '<=', record.deadline),
                    ('state', '=', 'posted'),
                    ('type', '=', 'out_invoice'),
                    ('bill_status', '!=', 'billed')
                ])
            else:
                invoice_ids = self.env['account.move'].search([
                    ('partner_id', 'in', res_partner_id.ids),
                    ('x_studio_date_invoiced', '<=', record.deadline),
                    ('state', '=', 'posted'),
                    ('type', '=', 'out_invoice'),
                    ('bill_status', '!=', 'billed')
                ])

            _line_compute_amount_tax = 0
            for invoice in invoice_ids:
                for line in invoice.invoice_line_ids:
                    if line.bill_status != 'billed':
                        if line.move_id.x_voucher_tax_transfer == 'foreign_tax' \
                                or line.move_id.x_voucher_tax_transfer == 'voucher':
                            _untax_amount = line.invoice_custom_lineamount
                            _tax = line.tax_rate * line.invoice_custom_lineamount / 100
                            _amount = _untax_amount + _tax
                        elif line.move_id.x_voucher_tax_transfer == 'internal_tax':
                            _untax_amount = line.invoice_custom_lineamount
                            _tax = 0
                            _amount = _untax_amount
                        elif line.move_id.x_voucher_tax_transfer == 'invoice':
                            _untax_amount = line.invoice_custom_lineamount
                            _tax = 0
                            _amount = _untax_amount + _tax
                            if line.product_id.product_tax_category == 'foreign':
                                _line_compute_amount_tax = _line_compute_amount_tax + (
                                        line.invoice_custom_lineamount * line.tax_rate / 100)
                            elif line.product_id.product_tax_category == 'internal':
                                _line_compute_amount_tax = _line_compute_amount_tax + 0
                            else:
                                _line_compute_amount_tax = _line_compute_amount_tax + 0
                        elif line.move_id.x_voucher_tax_transfer == 'custom_tax':
                            _untax_amount = line.invoice_custom_lineamount
                            _tax = 0
                            _amount = _untax_amount

                        if line.move_id.x_voucher_tax_transfer != 'voucher':
                            if record.customer_tax_rounding == 'round':
                                _untax_amount = int(round(_untax_amount, 1) + 0.5)
                                _tax = int(round(_tax, 1) + 0.5)
                                _amount = int(round(_amount, 1) + 0.5)
                            elif record.customer_tax_rounding == 'roundup':
                                _untax_amount = math.ceil(_untax_amount)
                                _tax = math.ceil(_tax)
                                _amount = math.ceil(_amount)
                            else:
                                _untax_amount = math.floor(_untax_amount)
                                _tax = math.floor(_tax)
                                _amount = math.floor(_amount)

                        _amount_untaxed = _amount_untaxed + _untax_amount
                        _tax_amount = _tax_amount + _tax
                        _amount_total = _amount_total + _amount

                if line.move_id.x_voucher_tax_transfer == 'voucher':
                    if record.customer_tax_rounding == 'round':
                        _amount_untaxed = int(round(_amount_untaxed, 1) + 0.5)
                        _tax_amount = int(round(_tax_amount, 1) + 0.5)
                        _amount_total = int(round(_amount_total, 1) + 0.5)
                    elif record.customer_tax_rounding == 'roundup':
                        _amount_untaxed = math.ceil(_amount_untaxed)
                        _tax_amount = math.ceil(_tax_amount)
                        _amount_total = math.ceil(_amount_total)
                    else:
                        _amount_untaxed = math.floor(_amount_untaxed)
                        _tax_amount = math.floor(_tax_amount)
                        _amount_total = math.floor(_amount_total)
                elif line.move_id.x_voucher_tax_transfer == 'custom_tax':
                    _tax_amount = invoice.amount_tax
                    _amount_total = _amount_total + _tax_amount
                elif line.move_id.x_voucher_tax_transfer == 'invoice':
                    if record.customer_tax_rounding == 'round':
                        _line_compute_amount_tax = int(round(_line_compute_amount_tax, 1) + 0.5)
                    elif record.customer_tax_rounding == 'roundup':
                        _line_compute_amount_tax = math.ceil(_line_compute_amount_tax)
                    else:
                        _line_compute_amount_tax = math.floor(_line_compute_amount_tax)

            _tax_amount = _tax_amount + _line_compute_amount_tax
            _amount_total = _amount_total + _line_compute_amount_tax
            # Compute data for billed_amount field
            _billed_amount = _amount_total + _balance_amount

            # Set data to fields
            record.last_billed_amount = _last_billed_amount
            record.deposit_amount = _deposit_amount
            record.balance_amount = _balance_amount
            record.amount_untaxed = _amount_untaxed
            record.tax_amount = _tax_amount
            record.billed_amount = _billed_amount
        return True

    @api.constrains('customer_code', 'customer_code_bill')
    def _check_billing_place(self):
        for record in self:
            # Customer has customer_code equal with customer_code_bill. This is a Billing Place
            if record.customer_code == record.customer_code_bill:
                record.billing_liabilities_flg = True
            else:
                record.billing_liabilities_flg = False

    # 前回締日
    last_closing_date = fields.Date(compute=_set_data_to_fields, readonly=True, store=False)

    # 締切日
    deadline = fields.Date(compute=_set_data_to_fields, readonly=True, store=False)

    # 前回請求金額
    last_billed_amount = fields.Float(compute=_set_data_to_fields, string='Last Billed Amount', readonly=True,
                                      store=False)

    # 入金額
    deposit_amount = fields.Float(compute=_set_data_to_fields, string='Deposit Amount', readonly=True, store=False)

    # 繰越金額
    balance_amount = fields.Float(compute=_set_data_to_fields, string='Balance Amount', readonly=True, store=False)

    # 御買上金額
    amount_untaxed = fields.Float(compute=_set_data_to_fields, string='Amount Untaxed', readonly=True, store=False)

    # 消費税
    tax_amount = fields.Float(compute=_set_data_to_fields, string='Tax Amount', readonly=True, store=False)

    # 今回請求金額
    billed_amount = fields.Float(compute=_set_data_to_fields, string='Billed Amount', readonly=True, store=False)

    # 売伝枚数
    voucher_number = fields.Integer(compute=_set_data_to_fields, readonly=True, store=False)

    # 事業部
    department = fields.Many2one('hr.department', compute=_set_data_to_fields, readonly=True, store=False)

    # Relational fields with account.move model
    bill_account_move_ids = fields.One2many('account.move', 'billing_place_id', string='Invoices')

    # Relational fields with account.move.line model
    bill_account_move_line_ids = fields.One2many('account.move.line', 'billing_place_id', string='Invoices Line')

    # Button [抜粋/Excerpt]
    def bm_bill_excerpt_button(self):
        res_partner_id = self.env["res.partner"].search(
            ['|', ('customer_code', '=', self.customer_code), ('customer_code_bill', '=', self.customer_code)])

        self.bill_account_move_ids = self._get_invoices_sales_by_partner_id(partner_id=res_partner_id.ids,
                                                                            last_closing_date=self.last_closing_date,
                                                                            deadline=self.deadline)

        self.bill_account_move_line_ids = self.env['account.move.line'].search([
            ('move_id', 'in', self.bill_account_move_ids.ids),
            ('partner_id', 'in', res_partner_id.ids),
            ('account_internal_type', '=', 'other'),
            ('bill_status', '!=', 'billed'),
        ])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Billing Details',
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'bill.details',
            'res_id': self.id,
            'views': [(self.env.ref('Maintain_Bill_Management.bm_bill_details_form').id, 'form')],
            'context': {'form_view_initial_mode': 'edit', 'bill_management_module': True,
                        'view_name': 'Billing Details',
                        'billing_code': self.customer_code,
                        'billing_name': self.name,
                        'bill_account_move_ids': self.bill_account_move_ids,
                        'bill_move_ids': self.bill_account_move_ids.ids,
                        'last_closing_date': self.last_closing_date,
                        'deadline': self.deadline,
                        },
        }

        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Billing Details',
        #     'view_mode': 'form',
        #     'target': 'current',
        #     'res_model': 'res.partner',
        #     'res_id': self.id,
        #     'views': [(self.env.ref('Maintain_Bill_Management.bm_bill_form').id, 'form')],
        #     'context': {'form_view_initial_mode': 'edit', 'bill_management_module': True,
        #                 'view_name': 'Billing Details',
        #                 'bill_account_move_ids': self.bill_account_move_ids,
        #                 'bill_move_ids': self.bill_account_move_ids.ids,
        #                 'last_closing_date': self.last_closing_date,
        #                 'deadline': self.deadline,
        #                 },
        # }

    def create_bill_for_invoice(self, argsSelectedData):
        for rec in argsSelectedData:
            if (rec['last_billed_amount'] + rec['deposit_amount'] + rec['balance_amount'] + rec['amount_untaxed'] \
                    + rec['tax_amount'] + rec['billed_amount'] == 0):
                continue

            if advanced_search.val_bill_search_deadline:
                rec['deadline'] = advanced_search.val_bill_search_deadline
            # Create data for bill_info
            partner_ids = self.env['res.partner'].search([('id', '=', rec['id'])])

            res_partner_id = self.env["res.partner"].search(
                ['|', ('customer_code', '=', rec['customer_code']), ('customer_code_bill', '=', rec['customer_code'])])

            invoice_ids = self._get_invoices_by_partner_id(partner_id=res_partner_id.ids,
                                                           last_closing_date=rec['last_closing_date'],
                                                           deadline=rec['deadline'])

            invoice_ids.write({
                'bill_status': 'billed'
            })
            self.env['account.move.line'].search([('move_id', 'in', invoice_ids.ids)]).write({
                'bill_status': 'billed'
            })

            _invoice_details_number = 0
            _sum_amount_tax_cashed = 0
            _sum_amount_untaxed_cashed = 0
            _sum_amount_total_cashed = 0
            for invoice in invoice_ids:
                _invoice_details_number = _invoice_details_number + self.env['account.move.line'].search_count(
                    [('move_id', '=', invoice.id)])
                if invoice.customer_trans_classification_code == 'cash':
                    _sum_amount_untaxed_cashed = _sum_amount_untaxed_cashed + invoice.amount_untaxed
                    _sum_amount_tax_cashed = _sum_amount_tax_cashed + invoice.amount_tax
                    _sum_amount_total_cashed = _sum_amount_total_cashed + invoice.amount_total

            payment_domain = [
                ('partner_id', 'in', res_partner_id.ids),
                ('payment_date', '<=', rec['deadline']),
                ('state', '=', 'draft'),
                ('bill_status', '!=', 'billed'),
            ]
            if rec.get('last_closing_date'):
                payment_domain += [('payment_date', '>', rec['last_closing_date'])]

            payment_ids = self.env['account.payment'].search(payment_domain)
            print('aaaaaaaaaaa', payment_ids)


            # payment_ids.write({
            #     'bill_status': 'billed'
            # })
            # payment_ids.post()

            _bill_no = self.env['ir.sequence'].next_by_code('bill.sequence')

            _bill_info_ids = self.env['bill.info'].create({
                'billing_code': rec['customer_code'],
                'billing_name': rec['name'],
                'bill_no': _bill_no,
                'bill_date': date.today(),
                'last_closing_date': rec['last_closing_date'],
                'closing_date': rec['deadline'],
                'deadline': rec['deadline'],
                'invoices_number': len(invoice_ids),
                'invoices_details_number': _invoice_details_number,
                'last_billed_amount': rec['last_billed_amount'],
                'deposit_amount': rec['deposit_amount'],
                'balance_amount': rec['balance_amount'],
                'amount_untaxed': rec['amount_untaxed'],
                'tax_amount': rec['tax_amount'],
                'amount_total': rec['billed_amount'] - rec['balance_amount'],
                'amount_untaxed_cashed': _sum_amount_tax_cashed,
                'tax_amount_cashed': _sum_amount_tax_cashed,
                'amount_total_cashed': _sum_amount_total_cashed,
                'billed_amount': rec['billed_amount'],
                'partner_id': partner_ids.id,
                'hr_employee_id': partner_ids.customer_agent.id,
                'hr_department_id': partner_ids.customer_agent.department_id.id,
                'business_partner_group_custom_id': partner_ids.customer_supplier_group_code.id,
                'customer_closing_date_id': partner_ids.customer_closing_date.id,
                'customer_excerpt_request': partner_ids.customer_except_request,
            })

            for invoice in invoice_ids:
                _bill_invoice_ids = self.env['bill.invoice'].create({
                    'bill_info_id': _bill_info_ids.id,
                    'billing_code': rec['customer_code'],
                    'billing_name': rec['name'],
                    'bill_no': _bill_no,
                    'bill_date': date.today(),
                    'last_closing_date': rec['last_closing_date'],
                    'closing_date': rec['deadline'],
                    'deadline': rec['deadline'],
                    'customer_code': invoice.partner_id.customer_code,
                    'customer_name': invoice.partner_id.name,
                    'amount_untaxed': invoice.amount_untaxed,
                    'amount_tax': invoice.amount_tax,
                    'amount_total': invoice.amount_total,
                    'customer_trans_classification_code': invoice.customer_trans_classification_code,
                    'account_move_id': invoice.id,
                    'hr_employee_id': partner_ids.customer_agent.id,
                    'hr_department_id': partner_ids.customer_agent.department_id.id,
                    'business_partner_group_custom_id': partner_ids.customer_supplier_group_code.id,
                    'customer_closing_date_id': partner_ids.customer_closing_date.id,
                    'x_voucher_tax_transfer': invoice.x_voucher_tax_transfer,
                    'invoice_date': invoice.x_studio_date_invoiced,
                    'invoice_no': invoice.x_studio_document_no,
                    'type': invoice.type,
                })

                for line in invoice.invoice_line_ids:
                    self.env['bill.invoice.details'].create({
                        'bill_info_id': _bill_info_ids.id,
                        'bill_invoice_id': _bill_invoice_ids.id,
                        'billing_code': rec['customer_code'],
                        'billing_name': rec['name'],
                        'bill_no': _bill_no,
                        'bill_date': date.today(),
                        'last_closing_date': rec['last_closing_date'],
                        'closing_date': rec['deadline'],
                        'deadline': rec['deadline'],
                        'customer_code': line.partner_id.customer_code,
                        'customer_name': line.partner_id.name,
                        'customer_trans_classification_code': invoice.customer_trans_classification_code,
                        'account_move_line_id': line.id,
                        'hr_employee_id': partner_ids.customer_agent.id,
                        'hr_department_id': partner_ids.customer_agent.department_id.id,
                        'business_partner_group_custom_id': partner_ids.customer_supplier_group_code.id,
                        'customer_closing_date_id': partner_ids.customer_closing_date.id,
                        'x_voucher_tax_transfer': _bill_invoice_ids.x_voucher_tax_transfer,
                        'invoice_date': line.date,
                        'invoice_no': line.invoice_no,
                        'tax_rate': line.tax_rate,
                        'quantity': line.quantity,
                        'price_unit': line.price_unit,
                        'tax_amount': line.line_tax_amount,
                        'line_amount': line.invoice_custom_lineamount,
                        'voucher_line_tax_amount': line.voucher_line_tax_amount,
                        'payment_id': line.payment_id,
                    })
            for payment in payment_ids:
                self.env['bill.invoice.details'].create({
                    'bill_info_id': _bill_info_ids.id,
                    # 'bill_invoice_id': _bill_invoice_ids.id,
                    'billing_code': rec['customer_code'],
                    'billing_name': rec['name'],
                    'bill_no': _bill_no,
                    'bill_date': date.today(),
                    'last_closing_date': rec['last_closing_date'],
                    'closing_date': rec['deadline'],
                    'deadline': rec['deadline'],
                    'customer_code': payment.partner_id.customer_code,
                    'customer_name': payment.partner_payment_name1,
                    'customer_trans_classification_code': 'sale',
                    # 'account_move_line_id': line.id,
                    'hr_employee_id': partner_ids.customer_agent.id,
                    'hr_department_id': partner_ids.customer_agent.department_id.id,
                    'business_partner_group_custom_id': partner_ids.customer_supplier_group_code.id,
                    'customer_closing_date_id': partner_ids.customer_closing_date.id,
                    # 'x_voucher_tax_transfer': _bill_invoice_ids.x_voucher_tax_transfer,
                    'quantity': 1,
                    'price_unit': payment.amount,
                    'invoice_date': payment.payment_date,
                    'invoice_no': payment.document_no,
                    'line_amount': payment.amount,
                    'payment_category': payment.vj_c_payment_category,
                })
            payment_ids.write({
                'bill_status': 'billed'
            })
            payment_ids.post()

        advanced_search.val_bill_search_deadline = ''
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def create_bill_details(self):
        ctx = self._context.copy()
        invoice_line_ids = self.env['account.move.line'].search([
            ('billing_place_id', '=', self.id),
            ('selected', '=', True),
            ('move_id', 'in', ctx.get('bill_move_ids')),
            ('bill_status', '=', 'not yet'),
        ])

        invoice_ids = self.env['account.move'].search([
            ('id', 'in', invoice_line_ids.move_id.ids),
            ('billing_place_id', '=', self.id),
        ])

        res_partner_id = self.env["res.partner"].search(
            ['|', ('customer_code', '=', self.customer_code),
             ('customer_code_bill', '=', self.customer_code)])

        invoice_cash_ids = self.env['account.move'].search([
            ('partner_id', 'in', res_partner_id.ids),
            ('x_studio_date_invoiced', '>', ctx.get('last_closing_date')),
            ('x_studio_date_invoiced', '<=', ctx.get('deadline')),
            ('state', '=', 'posted'),
            ('type', '=', 'out_invoice'),
            ('bill_status', '!=', 'billed'),
            ('customer_trans_classification_code', '=', 'cash'),
        ])

        _sum_amount_tax = 0
        _sum_amount_total = 0
        _sum_amount_untaxed = 0
        _invoice_details_number = 0
        _sum_amount_tax_cashed = 0
        _sum_amount_untaxed_cashed = 0
        _sum_amount_total_cashed = 0
        _untax_amount_voucher = 0
        _tax_voucher = 0
        _amount_voucher = 0
        _line_compute_amount_tax = 0
        # for line in invoice_line_ids:
        #     _sum_amount_untaxed = _sum_amount_untaxed + line.invoice_custom_lineamount
        #     _sum_amount_tax = _sum_amount_tax + line.line_tax_amount
        #     _sum_amount_total = _sum_amount_total + line.invoice_custom_lineamount + line.line_tax_amount
        #     if line.move_id.x_voucher_tax_transfer == 'invoice':
        #         if line.product_id.product_tax_category == 'foreign':
        #             _line_compute_amount_tax = _line_compute_amount_tax + (
        #                     line.invoice_custom_lineamount * line.tax_rate / 100)
        #         elif line.product_id.product_tax_category == 'internal':
        #             _line_compute_amount_tax = _line_compute_amount_tax + 0
        #         else:
        #             _line_compute_amount_tax = _line_compute_amount_tax + 0
        # if line.partner_id.customer_tax_rounding == 'round':
        #     _line_compute_amount_tax = round(_line_compute_amount_tax)
        # elif line.partner_id.customer_tax_rounding == 'roundup':
        #     _line_compute_amount_tax = math.ceil(_line_compute_amount_tax)
        # else:
        #     _line_compute_amount_tax = math.floor(_line_compute_amount_tax)
        # _sum_amount_tax = _sum_amount_tax + _line_compute_amount_tax
        # _sum_amount_total = _sum_amount_total + _line_compute_amount_tax

        for line in invoice_line_ids:
            _untax_amount = 0
            _tax = 0
            _amount = 0
            if line.bill_status != 'billed':
                if line.move_id.x_voucher_tax_transfer == 'foreign_tax':
                    _untax_amount = line.invoice_custom_lineamount
                    _tax = line.tax_rate * line.invoice_custom_lineamount / 100
                    _amount = _untax_amount + _tax
                elif line.move_id.x_voucher_tax_transfer == 'internal_tax':
                    _untax_amount = line.invoice_custom_lineamount
                    _tax = 0
                    _amount = _untax_amount
                elif line.move_id.x_voucher_tax_transfer == 'invoice':
                    _untax_amount = line.invoice_custom_lineamount
                    _tax = 0
                    _amount = _untax_amount + _tax
                    if line.product_id.product_tax_category == 'foreign':
                        _line_compute_amount_tax = _line_compute_amount_tax + (
                                line.invoice_custom_lineamount * line.tax_rate / 100)
                    elif line.product_id.product_tax_category == 'internal':
                        _line_compute_amount_tax = _line_compute_amount_tax + 0
                    else:
                        _line_compute_amount_tax = _line_compute_amount_tax + 0
                elif line.move_id.x_voucher_tax_transfer == 'custom_tax':
                    _untax_amount = line.invoice_custom_lineamount
                    _tax = 0
                    _amount = _untax_amount
                elif line.move_id.x_voucher_tax_transfer == 'voucher':
                    _untax_amount_voucher = line.invoice_custom_lineamount
                    _tax_voucher = line.tax_rate * line.invoice_custom_lineamount / 100
                    _amount_voucher = _untax_amount_voucher + _tax_voucher

                if line.move_id.x_voucher_tax_transfer != 'voucher':
                    if line.move_id.customer_tax_rounding == 'round':
                        _untax_amount = round(_untax_amount)
                        _tax = round(_tax)
                        _amount = round(_amount)
                    elif line.move_id.customer_tax_rounding == 'roundup':
                        _untax_amount = math.ceil(_untax_amount)
                        _tax = math.ceil(_tax)
                        _amount = math.ceil(_amount)
                    else:
                        _untax_amount = math.floor(_untax_amount)
                        _tax = math.floor(_tax)
                        _amount = math.floor(_amount)

                _sum_amount_untaxed = _sum_amount_untaxed + _untax_amount
                _sum_amount_tax = _sum_amount_tax + _tax
                _sum_amount_total = _sum_amount_total + _amount

        if _untax_amount_voucher:
            if self.customer_tax_rounding == 'round':
                _untax_amount_voucher = int(round(_untax_amount_voucher, 1) + 0.5)
                _tax_voucher = int(round(_tax_voucher, 1) + 0.5)
                _amount_voucher = int(round(_amount_voucher, 1) + 0.5)
            elif self.customer_tax_rounding == 'roundup':
                _untax_amount_voucher = math.ceil(_untax_amount_voucher)
                _tax_voucher = math.ceil(_tax_voucher)
                _amount_voucher = math.ceil(_amount_voucher)
            else:
                _untax_amount_voucher = math.floor(_untax_amount_voucher)
                _tax_voucher = math.floor(_tax_voucher)
                _amount_voucher = math.floor(_amount_voucher)

        _sum_amount_untaxed = _sum_amount_untaxed + _untax_amount_voucher
        _sum_amount_tax = _sum_amount_tax + _tax_voucher
        _sum_amount_total = _sum_amount_total + _amount_voucher
        # if line.move_id.x_voucher_tax_transfer == 'voucher':
        #     if record.customer_tax_rounding == 'round':
        #         _amount_untaxed = int(round(_amount_untaxed, 1) + 0.5)
        #         _tax_amount = int(round(_tax_amount, 1) + 0.5)
        #         _amount_total = int(round(_amount_total, 1) + 0.5)
        #     elif record.customer_tax_rounding == 'roundup':
        #         _amount_untaxed = math.ceil(_amount_untaxed)
        #         _tax_amount = math.ceil(_tax_amount)
        #         _amount_total = math.ceil(_amount_total)
        #     else:
        #         _amount_untaxed = math.floor(_amount_untaxed)
        #         _tax_amount = math.floor(_tax_amount)
        #         _amount_total = math.floor(_amount_total)
        # elif line.move_id.x_voucher_tax_transfer == 'custom_tax':
        #     _tax_amount = invoice.amount_tax
        #     _amount_total = _amount_total + _tax_amount
        # elif line.move_id.x_voucher_tax_transfer == 'invoice':
        #     if record.customer_tax_rounding == 'round':
        #         _line_compute_amount_tax = int(round(_line_compute_amount_tax, 1) + 0.5)
        #     elif record.customer_tax_rounding == 'roundup':
        #         _line_compute_amount_tax = math.ceil(_line_compute_amount_tax)
        #     else:
        #         _line_compute_amount_tax = math.floor(_line_compute_amount_tax)
        #
        # _tax_amount = _tax_amount + _line_compute_amount_tax
        # _amount_total = _amount_total + _line_compute_amount_tax

        for invoice in invoice_cash_ids:
            _sum_amount_untaxed = _sum_amount_untaxed + invoice.amount_untaxed
            _sum_amount_tax = _sum_amount_tax + invoice.amount_tax
            _sum_amount_total = _sum_amount_total + invoice.amount_total
            _sum_amount_untaxed_cashed = _sum_amount_untaxed_cashed + invoice.amount_untaxed
            _sum_amount_tax_cashed = _sum_amount_tax_cashed + invoice.amount_tax
            _sum_amount_total_cashed = _sum_amount_total_cashed + invoice.amount_total

        bill_info_ids = self.env['bill.info'].search([('billing_code', '=', self.customer_code),
                                                      ('closing_date', '=', self.last_closing_date),
                                                      ('active_flag', '=', True)], order='deadline desc, bill_no desc',
                                                     limit=1)
        _last_billed_amount = 0
        if bill_info_ids:
            _last_billed_amount = bill_info_ids.billed_amount

        payment_ids = self.env['account.payment'].search([
            ('partner_id', 'in', res_partner_id.ids),
            ('payment_date', '>', self.last_closing_date),
            ('payment_date', '<=', self.deadline),
            ('state', '=', 'posted'),
            ('bill_status', '!=', 'billed'),
        ])
        _deposit_amount = 0
        for payment_id in payment_ids:
            _deposit_amount = _deposit_amount + payment_id.payment_amount

        _balance_amount = _last_billed_amount - _deposit_amount

        _bill_no = self.env['ir.sequence'].next_by_code('bill.sequence')

        invoice_line_ids.write({
            'bill_status': 'billed'
        })

        for invoice in invoice_ids:
            is_billed_invoice = True
            for line in invoice.invoice_line_ids:
                if line.bill_status == 'not yet':
                    is_billed_invoice = False
                    break
            if is_billed_invoice:
                invoice.write({
                    'bill_status': 'billed'
                })

        _bill_info_ids = self.env['bill.info'].create({
            'billing_code': self.customer_code,
            'billing_name': self.name,
            'bill_no': _bill_no,
            'bill_date': date.today(),
            'last_closing_date': ctx.get('last_closing_date'),
            'closing_date': ctx.get('deadline'),
            'deadline': ctx.get('deadline'),
            'invoices_number': len(invoice_ids),
            'invoices_details_number': _invoice_details_number,
            'last_billed_amount': _last_billed_amount,
            'deposit_amount': _deposit_amount,
            'balance_amount': _balance_amount,
            'amount_untaxed': _sum_amount_untaxed,
            'tax_amount': _sum_amount_tax,
            'amount_total': _sum_amount_total,
            'amount_untaxed_cashed': _sum_amount_tax_cashed,
            'tax_amount_cashed': _sum_amount_tax_cashed,
            'amount_total_cashed': _sum_amount_total_cashed,
            'billed_amount': _sum_amount_total + _balance_amount,
            'partner_id': self.id,
            'hr_employee_id': self.customer_agent.id,
            'hr_department_id': self.customer_agent.department_id.id,
            'business_partner_group_custom_id': self.customer_supplier_group_code.id,
            'customer_closing_date_id': self.customer_closing_date.id,
            'customer_excerpt_request': self.customer_except_request,
        })

        for invoice in invoice_ids:
            _bill_invoice_ids = self.env['bill.invoice'].create({
                'bill_info_id': _bill_info_ids.id,
                'billing_code': self.customer_code,
                'billing_name': self.name,
                'bill_no': _bill_no,
                'bill_date': date.today(),
                'last_closing_date': ctx.get('last_closing_date'),
                'closing_date': ctx.get('deadline'),
                'deadline': ctx.get('deadline'),
                'customer_code': invoice.partner_id.customer_code,
                'customer_name': invoice.partner_id.name,
                'amount_untaxed': invoice.amount_untaxed,
                'amount_tax': invoice.amount_tax,
                'amount_total': invoice.amount_total,
                'customer_trans_classification_code': invoice.customer_trans_classification_code,
                'account_move_id': invoice.id,
                'hr_employee_id': self.customer_agent.id,
                'hr_department_id': self.customer_agent.department_id.id,
                'business_partner_group_custom_id': self.customer_supplier_group_code.id,
                'customer_closing_date_id': self.customer_closing_date.id,
                'invoice_date': invoice.x_studio_date_invoiced,
                'invoice_no': invoice.x_studio_document_no,
                'type': invoice.type,
            })

        for line in invoice_line_ids:
            self.env['bill.invoice.details'].create({
                'bill_info_id': _bill_info_ids.id,
                'bill_invoice_id': _bill_invoice_ids.id,
                'billing_code': self.customer_code,
                'billing_name': self.name,
                'bill_no': _bill_no,
                'bill_date': date.today(),
                'last_closing_date': ctx.get('last_closing_date'),
                'closing_date': ctx.get('deadline'),
                'deadline': ctx.get('deadline'),
                'customer_code': line.partner_id.customer_code,
                'customer_name': line.partner_id.name,
                'customer_trans_classification_code': line.move_id.customer_trans_classification_code,
                'account_move_line_id': line.id,
                'hr_employee_id': self.customer_agent.id,
                'hr_department_id': self.customer_agent.department_id.id,
                'business_partner_group_custom_id': self.customer_supplier_group_code.id,
                'customer_closing_date_id': self.customer_closing_date.id,
                'invoice_date': line.date,
                'invoice_no': line.invoice_no,
                'payment_id': line.payment_id,
            })
        advanced_search.val_bill_search_deadline = ''
        self.ensure_one()
        action = self.env.ref('Maintain_Bill_Management.actions_bm_bill').read()[0]
        return action

    def check_all_button(self):
        ctx = self._context.copy()
        invoice_line_ids = self.env['account.move.line'].search([
            ('billing_place_id', '=', self.id),
            ('move_id', 'in', ctx.get('bill_move_ids')),
        ])
        invoice_line_ids.write({
            'selected': True
        })
        return True

    def uncheck_all_button(self):
        ctx = self._context.copy()
        invoice_line_ids = self.env['account.move.line'].search([
            ('billing_place_id', '=', self.id),
            ('move_id', 'in', ctx.get('bill_move_ids')),
        ])
        invoice_line_ids.write({
            'selected': False
        })

        return True


class InvoiceLineClass(models.Model):
    _inherit = 'account.move.line'

    billing_place_id = fields.Many2one('res.partner')

    bill_status = fields.Char(default="not yet")

    selected = fields.Boolean(default=False)

    def compute_data(self):
        for record in self:
            record.customer_code = record.partner_id.customer_code
            record.customer_name = record.partner_id.name

    customer_code = fields.Char(compute=compute_data, string='Customer Code', store=False)
    customer_name = fields.Char(compute=compute_data, string='Customer Name', store=False)
