from PIL.ImageStat import Global

from odoo import api, fields, models

search_x_studio_date_invoiced_from = ''
search_x_studio_date_invoiced_to = ''
search_x_studio_document_no = ''
search_name = ''
search_invoice_partner_display_name = ''
search_x_studio_name = ''


class PrintCollationHistory(models.Model):
    _inherit = 'bill.info'

    search_x_studio_date_invoiced_from = fields.Date('Search Date From', compute='_set_search_field', store=False)
    search_x_studio_date_invoiced_to = fields.Date('Search Date To', compute='_set_search_field', store=False)
    search_x_studio_document_no = fields.Char('Search Customer Code', compute='_set_search_field', store=False)
    search_name = fields.Char('Search Customer Name', compute='_set_search_field', store=False)
    search_invoice_partner_display_name = fields.Char('Search Bill Code', compute='_set_search_field', store=False)
    search_x_studio_name = fields.Char('Search Bil ')

    def _set_search_field(self):
        for search in self:
            search.search_x_studio_date_invoiced_from = search_x_studio_date_invoiced_from
            search.search_x_studio_date_invoiced_to = search_x_studio_date_invoiced_to
            search.search_x_studio_document_no = search_x_studio_document_no
            search.search_name = search_name
            search.search_invoice_partner_display_name = search_invoice_partner_display_name
            search.search_x_studio_name = search_x_studio_name

    def report_dialog(self):
        return {
            'type': ''
        }

    # Custom preview invoice
    def preview_invoice(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Maintain_Collation_History.collation_history_report',
            'model': 'bill.ifo',
            'report_type': "qweb-html",
        }

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        odoo/models.py
        """

        global search_x_studio_date_invoiced_from
        global search_x_studio_date_invoiced_to
        global search_x_studio_document_no
        global search_name
        global search_invoice_partner_display_name
        global search_x_studio_name
        search_x_studio_date_invoiced_from = ''
        search_x_studio_date_invoiced_to = ''
        search_x_studio_document_no = ''
        search_name = ''
        search_invoice_partner_display_name = ''
        search_x_studio_name = ''

        domain = []

        print(args)

        for se in args:
            if se[0] == 'last_closing_date' and se[1] == '>=':
                search_x_studio_date_invoiced_from = se[2]
            if se[0] == 'last_closing_date' and se[1] == '<=':
                search_x_studio_date_invoiced_to = se[2]
            if se[0] == "billing_code":
                search_x_studio_document_no = se[2]
            if se[0] == "billing_name":
                search_name = se[2]
            if se[0] == "bill_no":
                search_invoice_partner_display_name = se[2]
            if se[0] == "invoices_number":
                search_x_studio_name = se[2]
            domain += [se]

        # search_x_studio_date_invoiced

        res = self._search(args=domain, offset=offset, limit=limit, order=order, count=count)
        return res if count else self.browse(res)
