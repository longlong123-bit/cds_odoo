# -*- coding: utf-8 -*-
from odoo import api, fields, models, modules
from odoo.exceptions import ValidationError


class ClassProductClass(models.Model):
    _name = 'product.class'

    name = fields.Char('Class Name')
    product_class_code = fields.Char('Class Code')
    product_class_rate = fields.Char('Discount Rate')
    product_level = fields.Selection([('lv1','1'), ('lv2','2'), ('lv3','3'), ('lv4','4')], string='Level')
    parent_code = fields.Selection([('code1','大分類'), ('code2','中分類'), ('code3','中小分類'), ('code5','小分類')], string="Parent Code")
    # product_parent_code = fields.Many2one('product.class', string="Parent Code")
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

    def name_get(self):
        result = []
        for rec in self:
            code = str(rec.product_class_code)
            result.append((rec.id, code))
        return result

    @api.model
    def get_values(self):
        res = super(ClassProductClass, self).get_values()
        res.update(
            parent_code=self.env['ir.config_parameter'].sudo().get_param(
                'product_class.parent_code')
        )
        return res

    def set_values(self):
        super(ClassProductClass, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        field1 = self.parent_code and self.parent_code.id or False
        param.set_param('product_class.parent_code', field1)

