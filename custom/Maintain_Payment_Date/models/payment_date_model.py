from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ClassPaymentDate(models.Model):
    _name = 'payment.date'

    name = fields.Char('Payment Date Name')
    payment_date = fields.Integer('Payment Date', size=2)
    payment_month = fields.Selection([('this_month', 'This Month'), ('next_month', 'Next Month'), ('two_months_after', 'Two Months After'),
                                      ('three_months_after', 'Three Months After'), ('four_months_after', 'Four Months After'), ('five_months_after', 'Five Months After'),
                                      ('six_months_after', 'Six Months After')], string='Payment Month', default='this_month')
    active = fields.Boolean('Active', default=True)

    @api.constrains('payment_date')
    def _check_maximum_day(self):
        if self.payment_date > 31 or self.payment_date < 1:
            raise ValidationError(_('The day must be 1 to 31!'))

    @api.constrains('name')
    def _check_unique_searchkey(self):
        exists = self.env['payment.date'].search(
            [('name', '=', self.name), ('id', '!=', self.id)])
        if exists:
            raise ValidationError(_('The name must be unique!'))
