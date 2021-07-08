from odoo import models, fields, api
from ...Maintain_Payment_Request_Bill.models import payment_request_bill

claim_zero = 0


class ListBillClass(models.Model):
    _inherit = 'bill.info'

    def _compute_customer_other_cd(self):
        for record in self:
            record.customer_other_cd = record.partner_id.customer_other_cd
            record.input_claim_zero = claim_zero
            record.search_list_claim_zero = payment_request_bill.search_list_claim_zero
            record.search_list_customer_closing_date_id = payment_request_bill.search_list_customer_closing_date_id
            record.search_list_closing_date = payment_request_bill.search_list_closing_date
            record.search_list_hr_department_id = payment_request_bill.search_list_hr_department_id
            record.search_list_hr_employee_id = payment_request_bill.search_list_hr_employee_id
            record.search_list_business_partner_group_custom_id = payment_request_bill.search_list_business_partner_group_custom_id
            record.search_list_billing_code_from = payment_request_bill.search_list_billing_code_from
            record.search_list_billing_code_to = payment_request_bill.search_list_billing_code_to
            record.search_list_display_order = payment_request_bill.search_list_display_order

    customer_other_cd = fields.Char(compute=_compute_customer_other_cd, readonly=True, store=False)

    input_claim_zero = fields.Char(compute=_compute_customer_other_cd, readonly=True, store=False)

    # search display
    search_list_customer_closing_date_id = fields.Char('search_list_customer_closing_date_id',
                                                       compute=_compute_customer_other_cd, store=False)
    search_list_closing_date = fields.Char('search_list_closing_date', compute=_compute_customer_other_cd, store=False)
    search_list_hr_department_id = fields.Char('search_list_hr_department_id', compute=_compute_customer_other_cd,
                                               store=False)
    search_list_hr_employee_id = fields.Char('search_list_hr_employee_id', compute=_compute_customer_other_cd,
                                             store=False)
    search_list_business_partner_group_custom_id = fields.Char('search_list_business_partner_group_custom_id',
                                                               compute=_compute_customer_other_cd, store=False)
    search_list_billing_code_from = fields.Char('search_list_billing_code_from', compute=_compute_customer_other_cd,
                                                store=False)
    search_list_billing_code_to = fields.Char('search_list_billing_code_to', compute=_compute_customer_other_cd,
                                              store=False)
    search_list_display_order = fields.Char('search_list_display_order', compute=_compute_customer_other_cd,
                                            store=False)
    search_list_claim_zero = fields.Char('search_list_claim_zero', compute=_compute_customer_other_cd, store=False)

    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     ctx = self._context.copy()
    #     global claim_zero
    #     claim_zero = 0
    #     domain = []
    #     if 'Billing List' == ctx.get('view_name'):
    #         for record in args:
    #             if record[0] == '&':
    #                 continue
    #             if 'display_order' == record[0]:
    #                 if record[2] == '0':
    #                     order = 'hr_employee_id'
    #                 else:
    #                     order = 'billing_code'
    #                 continue
    #             if 'claim_zero' == record[0]:
    #                 if record[2] == 'True':
    #                     claim_zero = 1
    #                 continue
    #             domain += [record]
    #     else:
    #         domain = args
    #
    #     res = self._search(domain, offset=offset, limit=limit, order=order, count=count)
    #     return res if count else self.browse(res)

    def search(self, args, offset=0, limit=None, order=None, count=False):
        module_context = self._context.copy()
        if module_context.get('have_advance_search') and module_context.get('bill_management_module'):
            domain = []
            billing_ids = []
            billing_query = []
            for arg in args:
                if 'billing_code' in arg:
                    billing_query.append("LOWER(billing_code) {0} '{1}'".format(arg[1], arg[2].lower()))
                else:
                    domain += [arg]
                    # billing_query.append("{0} {1} '{2}'".format(arg[0], arg[1], arg[2]))

            if billing_query:
                query = 'SELECT id FROM bill_info WHERE ' + ' AND '.join(billing_query)
                self._cr.execute(query)
                query_res = self._cr.dictfetchall()
                for bill_record in query_res:
                    billing_ids.append(bill_record.get('id'))
                domain += [['id', 'in', billing_ids]]
            args = domain
        res = super(ListBillClass, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res
