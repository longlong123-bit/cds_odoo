# -*- coding: utf-8 -*-
from addons.account.models.product import ProductTemplate
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError



class ReceiptDivide(models.Model):
    _name = 'receipt.divide.custom'

    def _get_default_client_id(self):
        return self.env["client.custom"].search([], limit=1, order='id').id

    def _get_default_organization_id(self):
        return self.env["res.company"].search([], limit=1, order='id').id

    client = fields.Many2one('client.custom', required=True, default=_get_default_client_id)
    search_key_receipt = fields.Char('searchkey', default=lambda self:_(''))
    organization = fields.Many2one('res.company', required=True, default=_get_default_organization_id)
    name = fields.Char('name', required=True)
    description =fields.Char('description')
    comment = fields.Char('comment')
    active = fields.Boolean('isactive', default=True)
    default = fields.Boolean('isactive', default=True)

    @api.constrains('search_key_receipt')
    def _check_unique_searchkey(self):
        exists = self.env['receipt.divide.custom'].search(
            [('search_key_receipt', '=', self.search_key_receipt), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The Search Key has already been registered'))

    @api.model
    def create(self, vals):
        # check search key
        if vals['search_key_receipt'] == False:
            vals['search_key_receipt'] = self.env['ir.sequence'].next_by_code('search.key.receipt.sequence') or _(' ')
        return super(ReceiptDivide, self).create(vals)




