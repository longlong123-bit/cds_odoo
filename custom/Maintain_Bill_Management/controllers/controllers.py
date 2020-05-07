from odoo import http
from odoo.http import request

class BillManagementController(http.Controller):
    @http.route('/billmanagement', auth='public')
    def index(self, **kw):
        # Instance of model bill
        bill_model = http.request.env['bm.bill'];
        invoices = bill_model.get_invoices([1])
        company = request.env.company

        return request.render('Maintain_Bill_Management.index', {
            'invoices': invoices,
            'company': company
        })