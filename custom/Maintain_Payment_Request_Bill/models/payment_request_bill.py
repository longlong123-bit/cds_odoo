# -*- coding: utf-8 -*-
from calendar import calendar
from datetime import date, timedelta

from odoo import api, fields, models, _

from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

ADDRESS_FIELDS = ('street', 'street2', 'address3', 'zip', 'city', 'state_id', 'country_id')

search_last_closing_date_from = ''
search_last_closing_date_to = ''
search_closing_date_from = ''
search_closing_date_to = ''
# search_billing_name = ''
search_bill_job_title = ''
search_bill_sale_rep = ''
search_billing_code_from = ''
search_billing_code_to = ''
search_address_type = ''
search_cash_type = ''
search_claim_type = ''
search_bill_group = ''
search_print_child = ''


class CollationPayment(models.Model):
    _inherit = 'bill.info'
    address_type = fields.Integer('address_type', default=1)
    cash_type = fields.Integer('cash_type', default=1)
    claim_type = fields.Integer('claim_type', default=1)
    search_last_closing_date_from = fields.Date('Last Closing Date From', compute='_set_search_field', store=False)
    search_last_closing_date_to = fields.Date('Last Closing Date To', compute='_set_search_field', store=False)
    search_closing_date_from = fields.Date('Closing Date From', compute='_set_search_field', store=False)
    search_closing_date_to = fields.Date('Closing Date To', compute='_set_search_field', store=False)
    # search_billing_name = fields.Char('billing_name', compute='_set_search_field', store=False)
    search_billing_code_from = fields.Char('billing_code_from', compute='_set_search_field', store=False)
    search_billing_code_to = fields.Char('billing_code_to', compute='_set_search_field', store=False)
    search_address_type = fields.Integer('billing_address', compute='_set_search_field', store=False)
    search_cash_type = fields.Integer('billing_Cash', compute='_set_search_field', store=False)
    search_claim_type = fields.Integer('billing_claim', compute='_set_search_field', store=False)
    search_bill_job_title = fields.Char('search_bill_job_title', compute='_set_search_field', store=False)
    search_bill_sale_rep = fields.Char('search_bill_sale_rep', compute='_set_search_field', store=False)
    search_bill_group = fields.Char('search_bill_group', compute='_set_search_field', store=False)
    search_print_child = fields.Integer('search_bill_group', compute='_set_search_field', store=False)

    bill_sale_rep = fields.Char('bill_sale_rep')
    sale_rep_id = fields.Many2one('res.users')
    hr_employee_id = fields.Many2one('hr.employee')
    bill_job_title = fields.Char('bill_job_title', compute='_set_bill_sale_rep')
    bill_group = fields.Char('bill_group', compute='_set_bill_group')

    def _set_bill_sale_rep(self):
        sale_rep_id = self.env['res.users'].search([('partner_id', '=', self.partner_id)])
        self.bill_sale_rep = sale_rep_id.name
        hr_employee_id = self.env['hr.employee'].search([('user_id', '=', self.sale_rep_id.id)])
        self.bill_job_title = hr_employee_id.job_title

    def _set_bill_group(self):
        for gr in self:
            gr.bill_group = gr.partner_id.group_supplier

    def _set_search_field(self):
        domain = []
        if search_bill_job_title:
            domain += [('id', '=', int(search_bill_job_title))]
        hr_employee_ids = []
        if domain:
            hr_employee_ids = self.env["hr.employee"].search(domain)
        # get array user_id from hr_employee_ids
        user_id = []
        for row in hr_employee_ids:
            if row.user_id.id:
                user_id.append(row.user_id.id)

        for search in self:
            search.search_last_closing_date_from = search_last_closing_date_from
            search.search_last_closing_date_to = search_last_closing_date_to
            search.search_closing_date_from = search_closing_date_from
            search.search_closing_date_to = search_closing_date_to
            # search.search_billing_name = search_billing_name
            search.search_billing_code_from = search_billing_code_from
            search.search_billing_code_to = search_billing_code_to
            search.search_address_type = search_address_type
            search.search_cash_type = search_cash_type
            search.search_claim_type = search_claim_type
            search.search_bill_job_title = search_bill_job_title
            search.search_bill_sale_rep = search_bill_sale_rep
            search.search_bill_group = search_bill_group
            search.search_print_child = search_print_child

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        odoo/models.py
        """

        ctx = self._context.copy()

        domain = []

        print(args)

        if ctx.get('view_code') == '0001':
            global search_last_closing_date_from
            global search_last_closing_date_to
            global search_closing_date_from
            global search_closing_date_to
            # global search_billing_name
            global search_billing_code_from
            global search_billing_code_to
            global search_address_type
            global search_cash_type
            global search_claim_type
            global search_bill_job_title
            global search_bill_sale_rep
            global search_bill_group
            global search_print_child
            search_last_closing_date_from = ''
            search_last_closing_date_to = ''
            search_closing_date_from = ''
            search_closing_date_to = ''
            search_billing_code_from = ''
            search_billing_code_to = ''
            search_address_type = ''
            search_cash_type = ''
            search_claim_type = ''
            search_bill_job_title = ''
            search_bill_sale_rep = ''
            search_bill_group = ''
            search_print_child = ''

            for se in args:
                if se[0] == 'last_closing_date' and se[1] == '>=':
                    search_last_closing_date_from = se[2]
                    domain += [se]
                if se[0] == 'last_closing_date' and se[1] == '<=':
                    search_last_closing_date_to = se[2]
                    domain += [se]
                if se[0] == 'closing_date' and se[1] == '>=':
                    search_closing_date_from = se[2]
                    domain += [se]
                if se[0] == 'closing_date' and se[1] == '<=':
                    search_closing_date_to = se[2]
                    domain += [se]
                if se[0] == 'billing_code' and se[1] == '>=':
                    search_billing_code_from = se[2]
                    domain += [se]
                if se[0] == 'billing_code' and se[1] == '<=':
                    search_billing_code_to = se[2]
                    domain += [se]
                # if se[0]=='bill_job_title':
                #     search_bill_job_title = se[2]
                #     domain +=[se]
                if se[0] == 'bill_job_title':
                    search_bill_job_title = se[2]
                    domain += [se]
                if se[0] == 'bill_sale_rep':
                    search_bill_sale_rep = se[2]
                    domain += [se]
                if se[0] == 'bill_group':
                    search_bill_group = se[2]
                    domain += [se]
                if se[0] == 'address_type':
                    search_address_type = se[2]
                    if se[2] == 1:
                        order = 'user_id'
                    else:
                        order = 'billing_code'
                if se[0] == 'cash_type':
                    search_cash_type = se[2]
                if se[0] == 'claim_type':
                    search_claim_type = se[2]
                if se[0] == 'print_child':
                    search_print_child = se[2]
                    print('seeeee', se[2])

                print('address_type', search_address_type)
                print('cash_type', search_cash_type)
                print('claim_type', search_claim_type)
                print('aaaaa', search_print_child)
        else:
            domain = args


            # domain += [se]

        # search_x_studio_date_invoiced

        res = self._search(args=domain, offset=offset, limit=limit, order=order, count=count)
        return res if count else self.browse(res)
