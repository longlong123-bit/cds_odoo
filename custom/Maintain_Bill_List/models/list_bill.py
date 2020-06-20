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
