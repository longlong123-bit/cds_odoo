from odoo import models, fields, api
from datetime import datetime, date, timedelta


class BillingDetailsClass(models.Model):
    _name = 'bill.details'

    def compute_billing_place_id(self):
        ctx = self._context.copy()
        self.billing_place_id = ctx.get('active_id')
        return True

    def compute_billing_code(self):
        ctx = self._context.copy()
        self.billing_code = ctx.get('billing_code')
        return True

    def compute_billing_name(self):
        ctx = self._context.copy()
        self.billing_name = ctx.get('billing_name')
        return True

    def compute_deadline(self):
        ctx = self._context.copy()
        self.deadline = ctx.get('deadline')
        return True

    def compute_last_closing_date(self):
        ctx = self._context.copy()
        self.deadline = ctx.get('last_closing_date')
        return True

    def get_bill_account_move_ids_domain(self):
        ctx = self._context.copy()
        domain = [
            ('partner_id.customer_code_bill', '=', ctx.get('billing_code')),
            ('x_studio_date_invoiced', '<=', self.deadline),
            ('state', '=', 'posted'),
            ('bill_status', '!=', 'billed')
        ]
        if ctx.get('last_closing_date'):
            domain.append([('x_studio_date_invoiced', '>', self.last_closing_date)])
        self.bill_account_move_ids = self.env['account.move'].search(domain)
        return True

    def get_bill_account_move_line_ids_domain(self):
        ctx = self._context.copy()
        domain = [
            ('move_id', 'in', self.bill_account_move_ids.ids),
            ('date', '<=', self.deadline),
            ('bill_status', '=', 'not yet'),
            ('parent_state', '=', 'posted'),
            ('credit', '!=', 0),
        ]
        if ctx.get('last_closing_date'):
            domain.append([('date', '>', self.last_closing_date)])
        self.bill_account_move_line_ids = self.env['account.move.line'].search(domain)
        return True

    billing_place_id = fields.Many2one('res.partner', string='Partner Ids', compute=compute_billing_place_id)
    billing_code = fields.Char(compute=compute_billing_code, string='Billing Code', readonly=True, store=False)
    billing_name = fields.Char(compute=compute_billing_name, string='Billing Name', readonly=True, store=False)
    deadline = fields.Date(compute=compute_deadline, string='Deadline', readonly=True, store=False)
    last_closing_date = fields.Date(compute=compute_last_closing_date, string='Last Closing Date', readonly=True,
                                    store=False)
    # Relational fields with account.move model
    # bill_account_move_ids = fields.One2many('account.move', 'billing_place_id', string='Invoice Ids',
    #                                         domain=get_bill_account_move_ids_domain)
    bill_account_move_ids = fields.One2many('account.move', 'partner_id', string='Invoice Ids',
                                            compute=get_bill_account_move_ids_domain)

    # Relational fields with account.move.line model
    # bill_account_move_line_ids = fields.One2many('account.move.line', 'billing_place_id', string='Invoice Line Ids',
    #                                              domain=get_bill_account_move_line_ids_domain)
    bill_account_move_line_ids = fields.One2many('account.move.line', 'partner_id', string='Invoice Line Ids',
                                                 compute=get_bill_account_move_line_ids_domain)

    def create_bill_details(self):
        print("account.move ==>", self.bill_account_move_ids)
        print("account.move.line ==>", self.bill_account_move_line_ids)
        for line in self.bill_account_move_line_ids:
            print(line.line_tax_amount)
            print(line.invoice_custom_lineamount)
        return True

    def check_all_button(self):
        self.bill_account_move_line_ids.write({
            'selected': True
        })
        return True

    def uncheck_all_button(self):
        self.bill_account_move_line_ids.write({
            'selected': False
        })
        return True
