from odoo import models, fields


class SeiKyuuDetailsLineClass(models.Model):
    _name = 'seikyuu.details.line'

    # Seikyuu Details ID
    seikyuu_details_id = fields.Many2one('seikyuu.details', string='Seikyuu Details ID')

    # Invoice
    invoice_id = fields.Many2one('account.move')

    # Selected
    selected = fields.Boolean(default=False)

    # 売上日付
    invoice_date = fields.Date(string="Invoice Date", related='invoice_id.x_studio_date_invoiced')

    # 伝票No
    invoice_no = fields.Char(string="Invoice No", related='invoice_id.x_studio_document_no')

    # 得意先コード
    customer_code = fields.Char(string="Customer Code",
                                related='invoice_id.x_studio_business_partner.customer_code')

    # 得意先名
    customer_name = fields.Char(string="Customer Name", related='invoice_id.x_studio_business_partner.name')

    # メーカー名
    # user_input = fields.Char(string="User Input", related='invoice_id.x_userinput_id')

    # Invoice line Ids
    invoice_line_ids = fields.One2many(related='invoice_id.invoice_line_ids')

    # 金額
    total_price = fields.Float(string='Total Price')
