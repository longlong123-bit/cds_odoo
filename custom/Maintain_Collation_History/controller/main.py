# -*- coding: utf-8 -*-
import odoo
import logging
import json
import cgi
from odoo.http import request

_logger = logging.getLogger(__name__)


class CollationHistoryCustomAPI(odoo.http.Controller):
    @odoo.http.route('/collation/get_customer_name', type='http', auth="public", sitemap=False, cors='*', csrf=False)
    def get_customer_name(self, **kwargs):
        customer_code = kwargs.get('content', False)
        customer_name = ''
        if not customer_code:
            return json.dumps({
                    "status": "ok",
                    "content": {
                        "customer_code": '',
                        "customer_name": '',
                    }
                })
        model_name = "res.partner"
        dbname = request.session.db
        try:
            registry = odoo.modules.registry.Registry(dbname)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                rec = env[model_name].search([('customer_code', 'like', str(customer_code))], limit=1)
                if rec:
                    customer_code = rec[0].customer_code
                    customer_name = rec[0].name
                response = {
                    "status": "ok",
                    "content": {
                        "customer_code": customer_code,
                        "customer_name": customer_name,
                    }
                }
        except Exception:
            response = {
                "status": "error",
                "content": "not found"
            }
        return json.dumps(response)

    @odoo.http.route('/collation/get_customer_list', type='http', auth="public", sitemap=False, cors='*', csrf=False)
    def get_customer_list(self, **kwargs):
        # billing_code = kwargs.get('billing_code', False)
        model_name = "res.partner"
        dbname = request.session.db
        try:
            registry = odoo.modules.registry.Registry(dbname)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                rec = env[model_name].search([])  # ([('customer_code', 'like', '%' + str(billing_code).upper() + '%')])
                customer_list = []
                for customer in rec:
                    if customer.customer_code:
                        customer_list.append({'value': customer.customer_code, 'name': customer.name})
                response = {
                    "status": "ok",
                    "customer_list": customer_list,
                }
        except Exception as err:
            print('Error:', err)
            response = {
                "status": "error",
                "customer_list": [],
            }
        return json.dumps(response)

    @odoo.http.route('/collation/get_billing_name', type='http', auth="public", sitemap=False, cors='*', csrf=False)
    def get_billing_name(self, **kwargs):
        billing_code = kwargs.get('content', False)
        billing_name = ''
        if not billing_code:
            return json.dumps({
                    "status": "ok",
                    "content": {
                        "billing_code": '',
                        "billing_name": '',
                    }
                })
        model_name = "res.partner"
        dbname = request.session.db
        try:
            registry = odoo.modules.registry.Registry(dbname)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                rec = env[model_name].search([('customer_code_bill', 'like', str(billing_code))], limit=1)
                if rec:
                    billing_code = rec[0].customer_code_bill
                    billing_name = rec[0].name
                response = {
                    "status": "ok",
                    "content": {
                        "billing_code": billing_code,
                        "billing_name": billing_name,
                    }
                }
        except Exception:
            response = {
                "status": "error",
                "content": "not found"
            }
        return json.dumps(response)

    @odoo.http.route('/collation/get_billing_list', type='http', auth="public", sitemap=False, cors='*', csrf=False)
    def get_billing_list(self, **kwargs):
        # billing_code = kwargs.get('billing_code', False)
        model_name = "res.partner"
        dbname = request.session.db
        try:
            registry = odoo.modules.registry.Registry(dbname)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                rec = env[model_name].search([])  # ([('customer_code', 'like', '%' + str(billing_code).upper() + '%')])
                billing_list = []
                for customer in rec:
                    if customer.customer_code_bill:
                        billing_list.append({'value': customer.customer_code_bill, 'name': customer.name})
                response = {
                    "status": "ok",
                    "billing_list": billing_list,
                }
        except Exception as err:
            print('Error:', err)
            response = {
                "status": "error",
                "billing_list": [],
            }
        return json.dumps(response)
