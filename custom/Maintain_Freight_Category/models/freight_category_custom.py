# -*- coding: utf-8 -*-
from addons.account.models.product import ProductTemplate
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError



class FreightCategory(models.Model):
    _name = 'freight.category.custom'

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id

    def _get_default_organization_id(self):
        return self.env["res.company"].search([], limit=1, order='id').id

    client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)
    search_key_freight = fields.Char('searchkey', default=lambda self:_(''))
    organization = fields.Many2one('res.company', required=True, default=_get_default_organization_id)
    name = fields.Char('name', required=True)
    description =fields.Char('description')
    comment = fields.Char('comment')
    active = fields.Boolean('isactive', default=True)

    @api.constrains('search_key_freight')
    def _check_unique_searchkey(self):
        exists = self.env['freight.category.custom'].search(
            [('search_key_freight', '=', self.search_key_freight), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The Search Key has already been registered'))

    @api.model
    def create(self, vals):
        # check search key
        if vals['search_key_freight'] == False:
            vals['search_key_freight'] = self.env['ir.sequence'].next_by_code('search.key.freight.sequence') or _(' ')
        return super(FreightCategory, self).create(vals)

    def name_get(self):
        result = []
        for record in self:
            search_key_show = str(record.name)
            result.append((record.id, search_key_show))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if not recs:
            recs = self.search([('search_key_freight', operator, name)] + args, limit=limit)
        return recs.name_get()

    # TH - custom
    @api.constrains('name')
    def onchange_name(self):
        cr = self.env.cr
        cr.execute(
            "UPDATE product_product SET product_maker_name = '" + self.name
            + "' WHERE product_custom_freight_category = '" + str(self.id) + "'"
        )
        return True
    # TH - done
