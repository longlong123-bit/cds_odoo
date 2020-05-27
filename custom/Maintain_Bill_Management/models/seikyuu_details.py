from odoo import models, fields


class SeiKyuuDetailsClass(models.Model):
    _name = 'seikyuu.details'

    def _get_seikyuu_code(self):
        if self.seikyuu_id:
            self.seikyuu_code = self.seikyuu_id.customer_code

    def _get_seikyuu_name(self):
        if self.seikyuu_id:
            self.seikyuu_name = self.seikyuu_id.name

    def _get_deadline(self):
        if self.seikyuu_id:
            self.deadline = self.seikyuu_id.create_date

    seikyuu_id = fields.Many2one('res.partner', string='Res Partner', required=True, readonly=True, auto_join=True,
                                 help="The move of this entry line.")

    # Status
    status = fields.Char()

    # 請求先コード
    seikyuu_code = fields.Char(compute=_get_seikyuu_code, string='Seikyuu Code', readonly=True, store=False)

    # 請求先名
    seikyuu_name = fields.Char(compute=_get_seikyuu_name, string='Seikyuu Name', readonly=True, store=False)

    # 締切日
    deadline = fields.Date(compute=_get_deadline, string='Deadline', readonly=True, store=False)

    # Seikyuu Details Line Fields
    seikyuu_details_line = fields.One2many('seikyuu.details.line', 'seikyuu_details_id',
                                           string='Seikyuu Details Line', index=True,
                                           auto_join=True, help="The move of this entry line.")

    # Test button
    def test_button(self):
        print(self.id)
        return True
