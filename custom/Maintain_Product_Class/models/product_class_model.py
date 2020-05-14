# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClassProductClass(models.Model):
    _name = 'product.class'

    name = fields.Char('Class Name')
    product_class_code = fields.Char('Class Code')
    product_class_rate = fields.Char('Discount Rate')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(product_class_code)', 'The code must be unique!')
    ]

    @api.constrains('product_class_code')
    def _check_unique_searchkey(self):
        exists = self.env['product.class'].search(
            [('product_class_code', '=', self.product_class_code), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The code must be unique!'))

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'product_class_code': False})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        if not self.product_class_code:
            raise ValidationError(_('The code must input!'))
        return super(ClassProductClass, self).copy(default)
