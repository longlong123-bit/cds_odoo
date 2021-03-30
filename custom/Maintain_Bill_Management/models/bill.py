import datetime

from odoo import models, fields, api
from datetime import datetime, date
from ...Maintain_Accounts_Receivable_Balance_List.models import accounts_receivable_balance_list as advanced_search
from ...Maintain_Invoice_Remake.models.invoice_customer_custom import rounding
import pytz

class BillingClass(models.Model):
    _inherit = 'res.partner'

    def _compute_closing_date_for_bill(self, record):
        _last_closing_date = ''
        _last_closing_date_display = ''
        _deadline = datetime.now().astimezone(pytz.timezone(self.env.user.tz))
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
            _last_closing_date_display = last_data_bill_info_ids.deadline

        if _last_closing_date:
            invoice_line_ids = self.env['account.move.line'].search([
                ('partner_id', 'in', res_partner_ids.ids),
                ('date', '<=', _last_closing_date),
                ('bill_status', '=', 'not yet'),
                ('account_internal_type', '=', 'other'),
                ('parent_state', '=', 'posted'),
            ])

            payment_ids = self.env['account.payment'].search([
                ('partner_id', 'in', res_partner_ids.ids),
                ('payment_date', '<=', _last_closing_date),
                ('state', '=', 'draft'),
                ('bill_status', '!=', 'billed'),
            ])

            if invoice_line_ids or payment_ids:
                _last_closing_date = last_data_bill_info_ids.last_closing_date

        closing_date = {
            'last_closing_date': _last_closing_date,
            'deadline': _deadline,
            'last_closing_date_display': _last_closing_date_display,
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
                record.last_closing_date_display = _closing_date['last_closing_date_display']

            # Set data for department field
            record.department = record.customer_agent.department_id.id

            # Compute data for last_billed_amount field
            bill_info_ids = self.env['bill.info'].search([('billing_code', '=', record.customer_code),
                                                          ('deadline', '<=', record.last_closing_date_display),
                                                          ('active_flag', '=', True)],
                                                         order="deadline desc, bill_no desc", limit=1)

            for bill in bill_info_ids:
                _last_billed_amount = bill.billed_amount

            # Compute data for amount_untaxed, tax_amount, billed_amount fields
            res_partner_id = self.env["res.partner"].search(['|', ('customer_code', '=', record.customer_code),
                                                             ('customer_code_bill', '=', record.customer_code)])

            invoice_ids = self._get_invoices_by_partner_id(partner_id=res_partner_id.ids,
                                                           last_closing_date=record.last_closing_date,
                                                           deadline=record.deadline)
            payment_ids_domain = [
                ('partner_id', 'in', res_partner_id.ids),
                ('payment_date', '<=', record.deadline),
                ('state', 'in', ['draft', 'sent']),
                ('bill_status', '!=', 'billed'),
            ]

            if record.last_closing_date:
                payment_ids_domain += [('payment_date', '>', record.last_closing_date)]

            payment_ids = self.env['account.payment'].search(payment_ids_domain)
            _payment_cost_and_discount = 0

            # Set data for voucher_number field
            if record.customer_except_request:
                record.voucher_number = len(invoice_ids.filtered(lambda l: l.selected))
            else:
                record.voucher_number = len(invoice_ids)

            # Compute data for deposit_amount field
            for payment_id in payment_ids:
                if payment_id.payment_amount:
                    _deposit_amount = _deposit_amount + payment_id.payment_amount
                for payment_line in payment_id.account_payment_line_ids:
                    if payment_line.receipt_divide_custom_id.name in ['手数料', '値引']:
                        _payment_cost_and_discount += payment_line.payment_amount
            # Compute data for balance_amount field
            _balance_amount = _last_billed_amount - _deposit_amount

            _line_compute_amount_tax = 0
            for invoice in invoice_ids:
                invoices_line_ids_list = invoice.invoice_line_ids
                if record.customer_except_request:
                    invoices_line_ids_list = invoice.invoice_line_ids.filtered(lambda l: l.selected)
                for line in invoices_line_ids_list:
                    if line.bill_status != 'billed':
                        if line.move_id.x_voucher_tax_transfer == 'foreign_tax' \
                                or line.move_id.x_voucher_tax_transfer == 'voucher':
                            _untax_amount = line.invoice_custom_lineamount
                            _tax = line.tax_rate * line.invoice_custom_lineamount / 100
                            _amount = _untax_amount + _tax

                            if line.x_invoicelinetype == '値引':
                                _payment_cost_and_discount -= _amount
                        elif line.move_id.x_voucher_tax_transfer == 'internal_tax':
                            _untax_amount = line.invoice_custom_lineamount
                            _tax = 0
                            _amount = _untax_amount

                            if line.x_invoicelinetype == '値引':
                                _payment_cost_and_discount -= _amount
                        elif line.move_id.x_voucher_tax_transfer == 'invoice':
                            _untax_amount = line.invoice_custom_lineamount
                            _tax = 0
                            _amount = _untax_amount + _tax

                            if line.x_invoicelinetype == '値引':
                                _payment_cost_and_discount -= _amount
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

                            if line.x_invoicelinetype == '値引':
                                _payment_cost_and_discount -= _amount
                        if line.move_id.x_voucher_tax_transfer != 'voucher':
                            _untax_amount = rounding(_untax_amount, 0, record.customer_tax_rounding)
                            _tax = rounding(_tax, 0, record.customer_tax_rounding)
                            _amount = rounding(_amount, 0, record.customer_tax_rounding)

                        _amount_untaxed = _amount_untaxed + _untax_amount
                        _tax_amount = _tax_amount + _tax
                        _amount_total = _amount_total + _amount

                if invoice.x_voucher_tax_transfer == 'voucher':
                    _amount_untaxed = rounding(_amount_untaxed, 0, record.customer_tax_rounding)
                    _tax_amount = rounding(_tax_amount, 0, record.customer_tax_rounding)
                    _amount_total = rounding(_amount_total, 0, record.customer_tax_rounding)
                elif invoice.x_voucher_tax_transfer == 'custom_tax':
                    if record.customer_except_request:
                        if invoice.invoice_line_ids == invoice.invoice_line_ids.filtered(lambda l: l.selected):
                            _tax_amount = invoice.amount_tax
                            _amount_total = _amount_total + _tax_amount
                    else:
                        _tax_amount = invoice.amount_tax
                        _amount_total = _amount_total + _tax_amount
                elif invoice.x_voucher_tax_transfer == 'invoice':
                    _line_compute_amount_tax = rounding(_line_compute_amount_tax, 0, record.customer_tax_rounding)

            _tax_amount = _tax_amount + _line_compute_amount_tax
            _amount_total = _amount_total + _line_compute_amount_tax
            # Compute data for billed_amount field
            _billed_amount = _amount_total + _balance_amount

            # Set data to fields
            record.last_billed_amount = _last_billed_amount
            record.deposit_amount = _deposit_amount
            record.payment_cost_and_discount = _payment_cost_and_discount
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
    last_closing_date = fields.Date(compute=_set_data_to_fields, readonly=True)

    # 前回締日 for display
    last_closing_date_display = fields.Date(compute=_set_data_to_fields, readonly=True)

    # 締切日
    deadline = fields.Date(compute=_set_data_to_fields, readonly=True)

    # 前回請求金額
    last_billed_amount = fields.Float(compute=_set_data_to_fields, string='Last Billed Amount', readonly=True,
                                      )

    # 入金額
    deposit_amount = fields.Float(compute=_set_data_to_fields, string='Deposit Amount', readonly=True)

    payment_cost_and_discount = fields.Float(compute=_set_data_to_fields, string='Payment Cost And Discount', readonly=True)

    # 繰越金額
    balance_amount = fields.Float(compute=_set_data_to_fields, string='Balance Amount', readonly=True)

    # 御買上金額
    amount_untaxed = fields.Float(compute=_set_data_to_fields, string='Amount Untaxed', readonly=True)

    # 消費税
    tax_amount = fields.Float(compute=_set_data_to_fields, string='Tax Amount', readonly=True)

    # 今回請求金額
    billed_amount = fields.Float(compute=_set_data_to_fields, string='Billed Amount', readonly=True)

    # 売伝枚数
    voucher_number = fields.Integer(compute=_set_data_to_fields, readonly=True)

    # 事業部
    department = fields.Many2one('hr.department', compute=_set_data_to_fields, readonly=True)

    # Button [抜粋/Excerpt]
    def bm_bill_excerpt_button(self):
        bill = self.env['bill.details'].create(
            {
                'billing_place_id': self.id,
                'billing_code': self.customer_code,
                'billing_name': self.name,
                'last_closing_date': self.last_closing_date,
                'deadline': self.deadline,
                'last_billed_amount': self.last_billed_amount,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Billing Details',
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'bill.details',
            'res_id': bill.id,
            'views': [(self.env.ref('Maintain_Bill_Management.bm_bill_details_form').id, 'form')],
            'context': {'form_view_initial_mode': 'edit', 'bill_management_module': True,
                        'view_name': 'Billing Details',
                        },
        }
    #TH - Save Payment Plan Date To Bill Info
    def create_bill_for_invoice(self, argsSelectedData):
        for rec in argsSelectedData:
            partner_ids = self.env['res.partner'].search([('id', '=', rec['id'])])
            # Compute Payment Date
            payment_date_day_cal = date.today().strftime('%d')
            payment_date_month_cal = date.today().strftime('%m')
            payment_date_year_cal = date.today().strftime('%Y')
            closing_date_count = datetime.strptime(rec['deadline'], '%Y-%m-%d').date()
            closing_date_year = closing_date_count.strftime('%Y')
            closing_date_month = closing_date_count.strftime('%m')
            closing_date_date = closing_date_count.strftime('%d')
            payment_date_month = partner_ids.customer_payment_date.payment_month
            payment_date_date = partner_ids.customer_payment_date.payment_date
            if payment_date_month == 'this_month':
                payment_date_day_cal = payment_date_date
                if int(closing_date_month) in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                    payment_date_day_cal = 30
                elif int(closing_date_month) == 2 and payment_date_day_cal >= 28:
                    payment_date_day_cal = 28
                if int(closing_date_date) < payment_date_day_cal:
                    payment_date_month_cal = int(closing_date_month)
                    payment_date_year_cal = int(closing_date_year)
                else:
                    if int(closing_date_month) == 12:
                        payment_date_month_cal = int(closing_date_month) - 11
                        payment_date_year_cal = int(closing_date_year) + 1
                    else:
                        payment_date_month_cal = int(closing_date_month) + 1
                        payment_date_year_cal = int(closing_date_year)
            elif payment_date_month == 'next_month':
                if int(closing_date_month) == 12:
                    payment_date_month_cal = int(closing_date_month) - 11
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 1
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'two_months_after':
                if int(closing_date_month) in (11, 12):
                    payment_date_month_cal = int(closing_date_month) - 10
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 2
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'three_months_after':
                if int(closing_date_month) in (10, 11, 12):
                    payment_date_month_cal = int(closing_date_month) - 9
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 3
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'four_months_after':
                if int(closing_date_month) in (9, 10, 11, 12):
                    payment_date_month_cal = int(closing_date_month) - 8
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 4
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'five_months_after':
                if int(closing_date_month) in (8, 9, 10, 11, 12):
                    payment_date_month_cal = int(closing_date_month) - 7
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 5
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            elif payment_date_month == 'six_months_after':
                if int(closing_date_month) in (7, 8, 9, 10, 11, 12):
                    payment_date_month_cal = int(closing_date_month) - 6
                    payment_date_year_cal = int(closing_date_year) + 1
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
                else:
                    payment_date_month_cal = int(closing_date_month) + 6
                    payment_date_year_cal = int(closing_date_year)
                    payment_date_day_cal = payment_date_date
                    if payment_date_month_cal in (4, 6, 9, 11) and payment_date_day_cal >= 30:
                        payment_date_day_cal = 30
                    elif payment_date_month_cal == 2 and payment_date_day_cal >= 28:
                        payment_date_day_cal = 28
            payment_date_str = str(payment_date_month_cal) + '/' + str(payment_date_day_cal) + '/' + str(
                payment_date_year_cal)
            payment_date_obj = datetime.strptime(payment_date_str, '%m/%d/%Y').date()
            rec['payment_plan_date'] = payment_date_obj

    #TH - done

            if (rec['last_billed_amount'] + rec['deposit_amount'] + rec['balance_amount'] + rec['amount_untaxed'] \
                + rec['tax_amount'] + rec['billed_amount'] == 0) or (
                    rec['last_closing_date'] and rec['last_closing_date'] > rec['deadline']):
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
            if rec['customer_except_request']:
                invoice_ids = invoice_ids.filtered(lambda l: l.selected)

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
                ('bill_status', '!=', 'billed'),
                ('state', 'in', ['draft', 'sent']),
            ]
            if rec.get('last_closing_date'):
                payment_domain += [('payment_date', '>', rec['last_closing_date'])]

            payment_ids = self.env['account.payment'].search(payment_domain)

            _bill_no = self.env['ir.sequence'].next_by_code('bill.sequence')

            _bill_info_ids = self.env['bill.info'].create({
                'billing_code': rec['customer_code'],
                'billing_name': rec['name'],
                'bill_no': _bill_no,
                'bill_date': datetime.now().astimezone(pytz.timezone(self.env.user.tz)),
                'last_closing_date': rec['last_closing_date'],
                'closing_date': rec['deadline'],
                'deadline': rec['deadline'],
                'invoices_number': len(invoice_ids),
                'invoices_details_number': _invoice_details_number,
                'last_billed_amount': rec['last_billed_amount'],
                'deposit_amount': rec['deposit_amount'],
                'payment_cost_and_discount': rec['payment_cost_and_discount'],
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
                'payment_plan_date': rec['payment_plan_date']
            })

            for invoice in invoice_ids:
                _bill_invoice_ids = self.env['bill.invoice'].create({
                    'bill_info_id': _bill_info_ids.id,
                    'billing_code': rec['customer_code'],
                    'billing_name': rec['name'],
                    'bill_no': _bill_no,
                    'bill_date': datetime.now().astimezone(pytz.timezone(self.env.user.tz)),
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
                    'x_studio_summary': invoice.x_studio_summary,
                })

                invoice_line_ids_list = invoice.invoice_line_ids
                if rec['customer_except_request']:
                    invoice_line_ids_list = invoice.invoice_line_ids.filtered(lambda l: l.selected and l.bill_status != 'billed')
                for line in invoice_line_ids_list:
                    self.env['bill.invoice.details'].create({
                        'bill_info_id': _bill_info_ids.id,
                        'bill_invoice_id': _bill_invoice_ids.id,
                        'billing_code': rec['customer_code'],
                        'billing_name': rec['name'],
                        'bill_no': _bill_no,
                        'bill_date': datetime.now().astimezone(pytz.timezone(self.env.user.tz)),
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
                    })
            for payment in payment_ids:
                self.env['bill.invoice.details'].create({
                    'bill_info_id': _bill_info_ids.id,
                    # 'bill_invoice_id': _bill_invoice_ids.id,
                    'billing_code': rec['customer_code'],
                    'billing_name': rec['name'],
                    'bill_no': _bill_no,
                    'bill_date': datetime.now().astimezone(pytz.timezone(self.env.user.tz)),
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
                    'quantity': 0,
                    'price_unit': payment.amount,
                    'invoice_date': payment.payment_date,
                    'invoice_no': payment.document_no,
                    'line_amount': payment.amount,
                    'payment_category': payment.vj_c_payment_category,
                    'payment_id': payment.id,
                })

            # Update bill_status for account_move table
            if rec['customer_except_request']:
                for invoice in invoice_ids:
                    if invoice.invoice_line_ids \
                            and invoice.invoice_line_ids == invoice.invoice_line_ids.filtered(lambda l: l.selected):
                        invoice_ids.write({
                            'bill_status': 'billed'
                        })
                # Update bill_status for account_move_line table
                self.env['account.move.line'].search(
                    [('move_id', 'in', invoice_ids.ids), ('selected', '=', True)]).write({
                        'bill_status': 'billed'
                    })
            else:
                invoice_ids.write({
                    'bill_status': 'billed'
                })
                # Update bill_status for account_move_line table
                self.env['account.move.line'].search([('move_id', 'in', invoice_ids.ids)]).write({
                    'bill_status': 'billed'
                })

            # Update bill_status for account_payment table
            payment_ids.write({
                'bill_status': 'billed'
            })
            payment_ids.filtered(lambda l: l.state == 'draft').post()

        advanced_search.val_bill_search_deadline = ''

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
            for record in args:
                if 'deadline' in record:
                    id_bill_info = self.env['bill.info'].search([('closing_date', '=', record[2])])
                    domain += [['id', 'not in', id_bill_info.partner_id.ids]]
                domain += [record]
            args = domain
        res = super(BillingClass, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res

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
