from PIL.ImageStat import Global

from odoo import api, fields, models
# import Maintain_Payment_Request_Bill.payment_request_bill
from ...Maintain_Payment_Request_Bill.models import payment_request_bill


class PrintCollationHistory(models.Model):
    _inherit = 'bill.info'

    def _set_search_field(self):
        for search in self:
            search.search_x_studio_deadline = payment_request_bill.search_x_studio_deadline
            search.search_x_studio_document_no = payment_request_bill.search_x_studio_document_no
            search.search_name = payment_request_bill.search_name
            search.search_invoice_partner_display_name = payment_request_bill.search_invoice_partner_display_name
            search.search_x_studio_name = payment_request_bill.search_x_studio_name

    search_x_studio_deadline = fields.Date('Search Deadline', compute=_set_search_field, store=False)
    search_x_studio_document_no = fields.Char('Search Customer Code', compute=_set_search_field)
    search_name = fields.Char('Search Customer Name', compute=_set_search_field, store=False)
    search_invoice_partner_display_name = fields.Char('Search Bill Code', compute=_set_search_field, store=False)
    search_x_studio_name = fields.Char('Search Bil ')

    def report_dialog(self):
        return {
            'type': ''
        }

    # Custom preview invoice
    def preview_invoice(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'Maintain_Collation_History.collation_history_report',
            'model': 'bill.info',
            'report_type': "qweb-html",
        }
