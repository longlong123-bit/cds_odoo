# -*- coding: utf-8 -*-
from calendar import calendar
from datetime import date, timedelta, datetime
from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.http import request

ADDRESS_FIELDS = ('street', 'street2', 'address3', 'zip', 'city', 'state_id', 'country_id')

# Payment Request Bill
search_bill_job_title = ''
search_bill_sale_rep = ''
search_address_type = ''
search_cash_type = ''
search_claim_type = ''
search_print_child = ''
search_payment_closing_date = datetime.today()

# Collation History
search_x_studio_deadline = ''
search_x_studio_document_no = 'a'
search_name = ''
search_invoice_partner_display_name = ''
search_x_studio_name = ''

# Billing List
search_list_claim_zero = ''
search_list_customer_closing_date_id = ''
search_list_closing_date = ''
search_list_hr_department_id = ''
search_list_hr_employee_id = ''
search_list_business_partner_group_custom_id = ''
search_list_billing_code_from = ''
search_list_billing_code_to = ''
search_list_display_order = ''


class CollationPayment(models.Model):
    _inherit = 'bill.info'
    address_type = fields.Integer('address_type', default=1, store=False)
    cash_type = fields.Integer('cash_type', default=1, store=False)
    claim_type = fields.Integer('claim_type', default=1, store=False)
    search_address_type = fields.Integer('billing_address', compute='_set_search_field', store=False)
    search_cash_type = fields.Integer('billing_Cash', compute='_set_search_field', store=False)
    search_claim_type = fields.Integer('billing_claim', compute='_set_search_field', store=False)
    search_print_child = fields.Integer('search_bill_group', compute='_set_search_field', store=False)
    bill_invoice_ids_test = fields.Char('billing_code_from', compute='_set_search_field', store=False)

    sale_rep_id = fields.Many2one('res.users')
    hr_employee_id = fields.Many2one('hr.employee')
    bill_job_title = fields.Char('bill_job_title', compute='_set_bill_sale_rep')

    request.session['print_all_bill_session'] = False

    def _set_bill_sale_rep(self):
        self.sale_rep_id = self.env['res.users'].search([('partner_id', '=', self.partner_id)])
        self.hr_employee_id = self.env['hr.employee'].search([('user_id', '=', self.sale_rep_id.id)])
        self.bill_job_title = self.hr_employee_id.job_title

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
            search.search_address_type = search_address_type
            search.search_cash_type = search_cash_type
            search.search_claim_type = search_claim_type
            search.search_bill_job_title = search_bill_job_title
            search.search_print_child = search_print_child

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        odoo/models.py
        """
        ctx = self._context.copy()

        # Click from Menu => Clear advance condition search from session
        if len(args) == 0:
            request.session['advance_search_condition'] = []
            request.session['print_all_bill_session'] = False

        if ctx.get('have_advance_search') or request.session['print_all_bill_session']:
            domain = []
            if ctx.get('view_code') == 'bill_report':
                global search_address_type
                global search_cash_type
                global search_claim_type
                global search_bill_job_title
                global search_print_child
                global search_payment_closing_date
                search_address_type = ''
                search_cash_type = ''
                search_claim_type = ''
                search_bill_job_title = ''
                search_print_child = ''
                search_payment_closing_date = datetime.today()
                # check = 0
                # arr = ["hr_department_id","hr_employee_id","business_partner_group_custom_id"]
                for se in args:
                    if se[0] =='&':
                        continue
                    if 'customer_closing_date_id' == se[0]:
                        if se[2].isnumeric():
                            se[0] = 'customer_closing_date_id.start_day'
                            se[1] = '='
                        domain += [se]
                    if se[0] == 'closing_date':
                        search_payment_closing_date = datetime.strptime(se[2], '%Y-%m-%d')
                        domain += [se]
                    if se[0] == 'partner_id.customer_closing_date.closing_date_code':
                        domain += [se]
                    if se[0] == 'billing_code' and se[1] == '>=':
                        domain += [se]
                    if se[0] == 'billing_code' and se[1] == '<=':
                        domain += [se]

                    if se[0] == 'hr_department_id':
                        search_bill_job_title = se[2]
                        domain += [se]
                    if se[0] == 'hr_employee_id':
                        domain += [se]
                    if se[0] == 'business_partner_group_custom_id':
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
                        if se[2] == '0':
                            domain += [['billed_amount', '!=', '0']]
                    if se[0] == 'print_child':
                        search_print_child = se[2]
                args = domain
            elif 'Cancel Billing' == ctx.get('view_name'):
                # check = 0
                # arr = ["customer_closing_date_id.start_day", "hr_department_id", "hr_employee_id",
                #        "business_partner_group_custom_id"]
                for se in args:
                    if se[0] == '&':
                        continue
                    # if se[0] == 'search_category' and se[2] == 'equal':
                    #     check = 1
                    # if check == 1 and se[0] in arr:
                    #     se[1] = '=ilike'
                    if 'customer_closing_date_id' == se[0]:
                        if se[2].isnumeric():
                            se[0] = 'customer_closing_date_id.start_day'
                            se[1] = '='
                        # domain += [se]
                    if 'customer_excerpt_request' == se[0]:
                        if se[2] == 'True':
                            se[2] = True
                            # domain += [se]
                        elif se[2] == 'False':
                            se[2] = False
                        else:
                            continue
                            # domain += [se]
                    # if se[0] == 'closing_date':
                    #     domain += [se]
                    # if se[0] == 'billing_code' and se[1] == '>=':
                    #     domain += [se]
                    # if se[0] == 'billing_code' and se[1] == '<=':
                    #     domain += [se]
                    # if se[0] == 'hr_department_id':
                    #     domain += [se]
                    # if se[0] == 'hr_employee_id':
                    #     domain += [se]
                    # if se[0] == 'business_partner_group_custom_id':
                    domain += [se]
                args = domain
            elif ctx.get('view_name') == 'Bill History':
                global search_x_studio_deadline
                global search_x_studio_document_no
                global search_name
                global search_invoice_partner_display_name
                global search_x_studio_name
                search_x_studio_deadline = ''
                search_x_studio_document_no = ''
                search_name = ''
                search_invoice_partner_display_name = ''
                search_x_studio_name = ''
                # check = 0
                # arr = ["billing_code", "billing_name", "bill_detail_ids.customer_code", "bill_detail_ids.customer_name"]
                for se in args:
                    if se[0] == '&':
                        continue
                    # if se[0] == 'search_category' and se[2] == 'equal':
                    #     check = 1
                    # if check == 1 and se[0] in arr:
                    #     se[1] = '=ilike'
                    if se[0] == "deadline":
                        search_x_studio_deadline = se[2]
                        domain += [se]
                    if se[0] == "billing_code":
                        search_x_studio_document_no = se[2]
                        domain += [se]
                    if se[0] == "billing_name":
                        search_name = se[2]
                        domain += [se]
                    if se[0] == "bill_detail_ids.customer_code":
                        search_invoice_partner_display_name = se[2]
                        domain += [se]
                    if se[0] == "bill_detail_ids.customer_name":
                        search_x_studio_name = se[2]
                        domain += [se]
                args = domain

            elif 'Billing List' == ctx.get('view_name'):
                global search_list_claim_zero
                global search_list_customer_closing_date_id
                global search_list_closing_date
                global search_list_hr_department_id
                global search_list_hr_employee_id
                global search_list_business_partner_group_custom_id
                global search_list_billing_code_from
                global search_list_billing_code_to
                global search_list_display_order
                search_list_claim_zero = ''
                search_list_customer_closing_date_id = ''
                search_list_closing_date = ''
                search_list_hr_department_id = ''
                search_list_hr_employee_id = ''
                search_list_business_partner_group_custom_id = ''
                search_list_billing_code_from = ''
                search_list_billing_code_to = ''
                search_list_display_order = ''
                domain = []
                # check = 0
                # arr = ["customer_closing_date_id.start_day", "hr_department_id", "hr_employee_id",
                #        "business_partner_group_custom_id"]
                for record in args:
                    if record[0] == '&':
                        continue
                    # if record[0] == 'search_category' and record[2] == 'equal':
                    #     check = 1
                    #
                    # if check == 1 and record[0] in arr:
                    #     record[1] = '=ilike'
                    if record[0] == 'customer_closing_date_id':
                        search_list_customer_closing_date_id = record[2]
                        if record[2].isnumeric():
                            record[0] = 'customer_closing_date_id.start_day'
                            record[1] = '='
                    if record[0] == 'closing_date':
                        search_list_closing_date = record[2]
                    if record[0] == 'hr_department_id':
                        search_list_hr_department_id = record[2]
                    if record[0] == 'hr_employee_id':
                        search_list_hr_employee_id = record[2]
                    if record[0] == 'business_partner_group_custom_id':
                        search_list_business_partner_group_custom_id = record[2]
                    if record[0] == 'billing_code' and record[1] == 'gte':
                        search_list_billing_code_from = record[2]
                    if record[0] == 'billing_code' and record[1] == 'lte':
                        search_list_billing_code_to = record[2]
                    if 'display_order' == record[0]:
                        search_list_display_order = record[2]
                        if record[2] == '0':
                            order = 'hr_employee_id'
                        else:
                            order = 'billing_code'
                        continue
                    if 'claim_zero' == record[0]:
                        search_list_claim_zero = record[2]
                        if record[2] == 'True':
                            claim_zero = 1
                        continue
                    # if record[0] != 'search_category':
                    domain += [record]
                args = domain

            elif 'Draft Bill History' == ctx.get('view_name'):
                for se in args:
                    if se[0] == '&':
                        continue
                    if 'customer_closing_date_id' == se[0]:
                        if se[2].isnumeric():
                            se[0] = 'customer_closing_date_id.start_day'
                            se[1] = '='
                    if 'customer_excerpt_request' == se[0]:
                        if se[2] == 'True':
                            se[2] = True
                            # domain += [se]
                        elif se[2] == 'False':
                            se[2] = False
                        else:
                            continue
                    domain += [se]
                args = domain

        # Save advance search condition to session
        # when advance search or print all bill
        if ctx.get('have_advance_search') or request.session['print_all_bill_session']:

            # Set advance condition search to session
            request.session['advance_search_condition'] = args

        if 'Cancel Billing' == ctx.get('view_name') and len(args) == 0:
            return []
        elif 'bill_report' == ctx.get('view_code') and len(args) == 0:
            return []
        elif 'Billing List' == ctx.get('view_name') and len(args) == 0:
            return []
        elif 'Bill History' == ctx.get('view_name') and len(args) == 0:
            return []
        elif 'Draft Bill History' == ctx.get('view_name') and len(args) == 0:
            return []

        # res = super(CollationPayment, self).search(args=domain, offset=offset, limit=limit, order=order, count=count)
        return super(CollationPayment, self).search(args, offset=offset, limit=limit, order=order, count=count)

    def print_all_bill_button(self, args, offset=0, limit=None, order=None, count=False):

        request.session['print_all_bill_session'] = True

        cond = request.session['advance_search_condition']

        if len(cond) > 0:
            bill_info_ids = self.env['bill.info'].search(cond)

            if len(bill_info_ids) > 0:

                request.session['print_all_bill_session'] = False
                return self.env.ref('Maintain_Payment_Request_Bill.report').report_action(self, config=False)

        request.session['print_all_bill_session'] = False

        return


class PrintAllBill(models.AbstractModel):
    _name = 'report.Maintain_Payment_Request_Bill.reports'

    @api.model
    def _get_report_values(self, docids, data):

        if docids:
            # Print Selected Bill
            bill_info_ids = self.env['bill.info'].search([
                ('id', 'in', docids)
            ])
        else:
            # Print All Bill
            bill_info_ids = []
            cond = request.session['advance_search_condition']
            if len(cond) > 0:
                bill_info_ids = self.env['bill.info'].search(cond)
                request.session['advance_search_condition'] = cond

        return {
            'docs': bill_info_ids
        }
