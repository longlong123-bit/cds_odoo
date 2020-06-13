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

class CollationPayment(models.Model):
    _inherit = 'bill.info'

    # def _run_demo(self):
    #     for a in self:
    #         a.bill_invoice_ids = self.env['bill.invoice'].search(
    #             [('billing_code', '=', a.billing_code), ('last_closing_date', '=', a.last_closing_date)])
    #         print('a.bill_invoice_ids')

    # action_run = fields.Char(compute='_run')

    # def _get_customer_other_cd(self):
    #     for cd in self:
    #         # if self.partner_id:
    #         cd.customer_other_cd = cd.partner_id.customer_other_cd
    #
    # # その他CD
    # customer_other_cd = fields.Char('Customer CD', readonly=True, compute='_get_customer_other_cd')

    search_last_closing_date_from = fields.Date('Last Closing Date From', compute='_set_search_field', store=False)
    search_last_closing_date_to = fields.Date('Last Closing Date To', compute='_set_search_field', store=False)
    search_closing_date_from = fields.Date('Closing Date From', compute='_set_search_field', store=False)
    search_closing_date_to = fields.Date('Closing Date To', compute='_set_search_field', store=False)

    def _set_search_field(self):
        for search in self:
            search.search_last_closing_date_from = search_last_closing_date_from
            search.search_last_closing_date_to = search_last_closing_date_to
            search.search_closing_date_from = search_closing_date_from
            search.search_closing_date_to = search_closing_date_to

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        odoo/models.py
        """

        global search_last_closing_date_from
        global search_last_closing_date_to
        global search_closing_date_from
        global search_closing_date_to
        search_last_closing_date_from = ''
        search_last_closing_date_to = ''
        search_closing_date_from = ''
        search_closing_date_to = ''

        domain = []

        print(args)

        for se in args:
            if se[0] == 'last_closing_date' and se[1] == '>=':
                search_last_closing_date_from = se[2]
            if se[0] == 'last_closing_date' and se[1] == '<=':
                search_last_closing_date_to = se[2]
            if se[0] == "closing_date":
                search_closing_date_from = se[2]
            if se[0] == "closing_date":
                search_closing_date_to = se[2]
            domain += [se]

        # search_x_studio_date_invoiced

        res = self._search(args=domain, offset=offset, limit=limit, order=order, count=count)
        return res if count else self.browse(res)
