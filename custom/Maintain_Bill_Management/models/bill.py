from odoo import models, fields, api
from datetime import date, timedelta
import calendar


class BillingClass(models.Model):
    _inherit = 'res.partner'

    @staticmethod
    def _compute_closing_date_for_bill(customer_closing_date):
        today = date.today()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        if today.month != 1:
            days_in_last_month = calendar.monthrange(today.year, today.month - 1)[1]
        else:
            days_in_last_month = calendar.monthrange(today.year - 1, 12)[1]
        _start = customer_closing_date.start_day

        if _start >= 28:
            _current_closing_date = today.replace(day=days_in_month)
            _last_closing_date = _current_closing_date - timedelta(days=days_in_month)
        else:
            if today.day <= _start:
                _current_closing_date = today.replace(day=_start)
                _last_closing_date = _current_closing_date - timedelta(days=days_in_last_month)
            else:
                _last_closing_date = today.replace(day=_start)
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
            ('bill_status', '!=', 'billed')
        ])

    def _get_invoices_sales_by_partner_id(self, partner_id, last_closing_date, deadline):
        return self.env['account.move'].search([
            ('partner_id', 'in', partner_id),
            ('x_studio_date_invoiced', '>', last_closing_date),
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

    @api.depends('customer_code', 'customer_code_bill')
    def _set_data_to_fields(self):
        for record in self:

            # Set data for last_closing_date field and deadline field
            if record.customer_closing_date:
                _closing_date = self._compute_closing_date_for_bill(customer_closing_date=record.customer_closing_date)
                record.last_closing_date = _closing_date['last_closing_date']
                record.deadline = _closing_date['current_closing_date']

            # Set data for voucher_number field
            record.voucher_number = self._compute_voucher_number(record=record)

            # Set data for department field
            record.department = record.customer_agent.department_id.id

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

    # 売伝枚数
    voucher_number = fields.Integer(compute=_set_data_to_fields, readonly=True, store=False)

    # Check customer is Billing Place
    billing_liabilities_flg = fields.Boolean(default=False)

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

        self.bill_account_move_line_ids = self.bill_account_move_ids.invoice_line_ids

        return {
            'type': 'ir.actions.act_window',
            'name': 'Billing Details',
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'res.partner',
            'res_id': self.id,
            'views': [(self.env.ref('Maintain_Bill_Management.bm_bill_form').id, 'form')],
            'context': {'form_view_initial_mode': 'edit', 'bill_management_module': True,
                        'view_name': 'Billing Details',
                        'bill_account_move_ids': self.bill_account_move_ids,
                        'bill_move_ids': self.bill_account_move_ids.ids,
                        },
        }

    def create_bill_for_invoice(self, argsSelectedData):
        for rec in argsSelectedData:
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

            _sum_amount_tax = 0
            _sum_amount_total = 0
            _sum_amount_untaxed = 0
            _invoice_details_number = 0
            _sum_amount_tax_cashed = 0
            _sum_amount_untaxed_cashed = 0
            _sum_amount_total_cashed = 0
            for invoice in invoice_ids:
                _sum_amount_untaxed = _sum_amount_untaxed + invoice.amount_untaxed
                _sum_amount_tax = _sum_amount_tax + invoice.amount_tax
                _sum_amount_total = _sum_amount_total + invoice.amount_total
                _invoice_details_number = _invoice_details_number + self.env['account.move.line'].search_count(
                    [('move_id', '=', invoice.id)])
                if invoice.customer_trans_classification_code == 'cash':
                    _sum_amount_untaxed_cashed = _sum_amount_untaxed_cashed + invoice.amount_untaxed
                    _sum_amount_tax_cashed = _sum_amount_tax_cashed + invoice.amount_tax
                    _sum_amount_total_cashed = _sum_amount_total_cashed + invoice.amount_total

            bill_info_ids = self.env['bill.info'].search([('billing_code', '=', rec['customer_code']),
                                                          ('last_closing_date', '=', rec['last_closing_date']),
                                                          ('active_flag', '=', True)])
            _last_billed_amount = 0
            if bill_info_ids:
                _last_billed_amount = bill_info_ids.billed_amount

            payment_ids = self.env['account.payment'].search([
                ('partner_id', 'in', res_partner_id.ids),
                ('payment_date', '>', rec['last_closing_date']),
                ('payment_date', '<=', rec['deadline']),
                ('state', '=', 'posted')
            ])

            _deposit_amount = 0
            for payment_id in payment_ids:
                _deposit_amount = _deposit_amount + payment_id.payment_amount

            _balance_amount = _last_billed_amount - _deposit_amount

            _bill_no = self.env['ir.sequence'].next_by_code('bill.sequence')

            _bill_info_ids = self.env['bill.info'].create({
                'billing_code': rec['customer_code'],
                'billing_name': rec['name'],
                'bill_no': _bill_no,
                'bill_date': date.today(),
                'last_closing_date': rec['last_closing_date'],
                'closing_date': rec['deadline'],
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
                        'customer_code': line.partner_id.customer_code,
                        'customer_name': line.partner_id.name,
                        'customer_trans_classification_code': invoice.customer_trans_classification_code,
                        'account_move_line_id': line.id,
                        'hr_employee_id': partner_ids.customer_agent.id,
                        'hr_department_id': partner_ids.customer_agent.department_id.id,
                        'business_partner_group_custom_id': partner_ids.customer_supplier_group_code.id,
                        'customer_closing_date_id': partner_ids.customer_closing_date.id,
                    })

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
        ])

        invoice_line_ids.write({
            'bill_status': 'billed'
        })

        invoice_ids = self.env['account.move'].search([
            ('id', 'in', invoice_line_ids.move_id.ids),
            ('billing_place_id', '=', self.id),
        ])
        invoice_ids.write({
            'bill_status': 'billed'
        })

        res_partner_id = self.env["res.partner"].search(
            ['|', ('customer_code', '=', self.customer_code),
             ('customer_code_bill', '=', self.customer_code)])

        _sum_amount_tax = 0
        _sum_amount_total = 0
        _sum_amount_untaxed = 0
        _invoice_details_number = 0
        _sum_amount_tax_cashed = 0
        _sum_amount_untaxed_cashed = 0
        _sum_amount_total_cashed = 0
        for line in invoice_line_ids:
            _sum_amount_untaxed = _sum_amount_untaxed + line.invoice_custom_lineamount
            # _sum_amount_tax = _sum_amount_tax + line.amount_tax
            _sum_amount_total = _sum_amount_total + line.invoice_custom_lineamount
            if self.env['account.move'].search(
                    [('id', '=', line.move_id.id)]).customer_trans_classification_code == 'cash':
                _sum_amount_untaxed_cashed = _sum_amount_untaxed_cashed + line.invoice_custom_lineamount
                # _sum_amount_tax_cashed = _sum_amount_tax_cashed + line.amount_tax
                _sum_amount_total_cashed = _sum_amount_total_cashed + line.invoice_custom_lineamount

        bill_info_ids = self.env['bill.info'].search([('billing_code', '=', self.customer_code),
                                                      ('last_closing_date', '=', self.last_closing_date),
                                                      ('active_flag', '=', True)])
        _last_billed_amount = 0
        if bill_info_ids:
            _last_billed_amount = bill_info_ids.billed_amount

        payment_ids = self.env['account.payment'].search([
            ('partner_id', 'in', res_partner_id.ids),
            ('payment_date', '>', self.last_closing_date),
            ('payment_date', '<=', self.deadline),
            ('state', '=', 'posted')
        ])
        _deposit_amount = 0
        for payment_id in payment_ids:
            _deposit_amount = _deposit_amount + payment_id.payment_amount

        _balance_amount = _last_billed_amount - _deposit_amount

        _bill_info_ids = self.env['bill.info'].create({
            'billing_code': self.customer_code,
            'billing_name': self.name,
            'bill_no': 'BIL/',
            'bill_date': date.today(),
            'last_closing_date': self.last_closing_date,
            'closing_date': self.deadline,
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
                'bill_no': 'BIL/',
                'bill_date': date.today(),
                'last_closing_date': self.last_closing_date,
                'closing_date': self.deadline,
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
            })

            for line in invoice_line_ids:
                self.env['bill.invoice.details'].create({
                    'bill_info_id': _bill_info_ids.id,
                    'bill_invoice_id': _bill_invoice_ids.id,
                    'billing_code': self.customer_code,
                    'billing_name': self.name,
                    'bill_no': 'BIL/',
                    'bill_date': date.today(),
                    'last_closing_date': self.last_closing_date,
                    'closing_date': self.deadline,
                    'customer_code': line.partner_id.customer_code,
                    'customer_name': line.partner_id.name,
                    'customer_trans_classification_code': invoice.customer_trans_classification_code,
                    'account_move_line_id': line.id,
                    'hr_employee_id': self.customer_agent.id,
                    'hr_department_id': self.customer_agent.department_id.id,
                    'business_partner_group_custom_id': self.customer_supplier_group_code.id,
                    'customer_closing_date_id': self.customer_closing_date.id,
                })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Billing',
            'view_mode': 'tree',
            'target': 'current',
            'res_model': 'res.partner',
            'res_id': False,
            'views': [(self.env.ref('Maintain_Bill_Management.bm_bill_tree').id, 'tree')],
            'domain': [('billing_liabilities_flg', '=', True)],
            'context': {'bill_management_module': True, 'view_name': 'Billing Details', },
        }

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

    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context.copy()
        if 'Billing' == ctx.get('view_name'):
            for record in args:
                if 'customer_except_request' == record[0]:
                    if record[2] == 'True':
                        record[2] = True
                    else:
                        record[2] = False

        res = self._search(args, offset=offset, limit=limit, order=order, count=count)
        return res if count else self.browse(res)


class InvoiceClass(models.Model):
    _inherit = 'account.move'

    billing_place_id = fields.Many2one('res.partner')

    bill_status = fields.Char(default="not yet")


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
