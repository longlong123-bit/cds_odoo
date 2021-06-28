# -*- coding: utf-8 -*-
import odoo
import logging
import json
import cgi
from odoo.http import request

_logger = logging.getLogger(__name__)

class SupplierLedgerInquiryCustomAPI(odoo.http.Controller):
    @odoo.http.route('/get_billing_name', type='http', auth="public", sitemap=False, cors='*', csrf=False)
    def get_billing_name(self, **kwargs):
        billing_code = kwargs.get('content', False)
        billing_name = ''
        model_name = "res.partner"
        dbname = request.session.db
        try:
            registry = odoo.modules.registry.Registry(dbname)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                rec = env[model_name].search([('customer_code', '=', str(billing_code).upper())], limit=1)
                if rec:
                    billing_name = rec[0].name
                response = {
                    "status": "ok",
                    "content": {
                        "billing_name": billing_name,
                    }
                }
        except Exception:
            response = {
                "status": "error",
                "content": "not found"
            }
        return json.dumps(response)
