# -*- coding: utf-8 -*-
import odoo
import logging
import json
import cgi
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentRequestAPI(odoo.http.Controller):
    @odoo.http.route('/closing_date', type='http', auth="public", sitemap=False, cors='*', csrf=False)
    def closing_date(self, **kwargs):
        closing_date = kwargs.get('content', False)
        model_name = "bill.info"
        dbname = request.session.db
        try:
            registry = odoo.modules.registry.Registry(dbname)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                rec = env[model_name].search([('partner_id.customer_closing_date.closing_date_code', '=', str(closing_date))], order='deadline desc', limit=1)
                response = {
                    "status": "ok",
                    "content": {
                        "deadline": str(rec[0].deadline),
                    }
                }
        except Exception:
            response = {
                "status": "error",
                "content": "not found"
            }
        return json.dumps(response)
