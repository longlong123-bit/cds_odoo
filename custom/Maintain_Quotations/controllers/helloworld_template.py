from odoo import http
from odoo.http import request


class QuotationsController(http.Controller):

    @http.route('/helloworld', auth='public')
    def helloworld(self, **kwargs):
        return request.render('Maintain_Quotations.helloworld')
        # return ('<h1>Hello World!</h1>')