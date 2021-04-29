from datetime import timedelta, time, datetime
from custom.Maintain_Invoice_Remake.models.invoice_customer_custom import rounding, get_tax_method
import pytz
import logging
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError

_logger = logging.getLogger(__name__)


class OrderManagement(models.Model):
    _name = "order.management"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _rec_name = 'rec_name'

    def _get_next_order_no(self):
        sequence = self.env['ir.sequence'].search(
            [('code', '=', 'order.management'), ('prefix', '=', 'ARO-')])
        next = sequence.get_next_char(sequence.number_next_actual)
        return next

    def get_default_current_date(self):
        _date_now = datetime.now()
        return _date_now.astimezone(pytz.timezone(self.env.user.tz))

    def _get_domain_x_userinput_id(self):
        cr = self.env.cr
        user_ids = []
        cr.execute(
            "SELECT id FROM res_groups WHERE (name='User: Only Customer Master And Product Master in New Master Menu' OR name='ユーザー：マスタ管理に得意先マスタと商品マスタがあるだけ') AND category_id=55")
        groups = cr.fetchall()
        for group_id in groups:
            cr.execute("SELECT uid FROM res_groups_users_rel WHERE gid = " + str(group_id[0]))
            user_uid = cr.fetchall()
            user_ids.append(user_uid[0][0])

        # Get users in group system
        res_users_group_system_ids = self.env['res.users'].search([('active', '=', True)]).filtered(
            lambda l: l.has_group('base.group_system'))

        domain = [('id', 'not in', user_ids),
                  ('id', 'not in', res_users_group_system_ids.ids)]
        return domain

    rec_name = fields.Char(store=False, default='修正')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    refer_quotation_history = fields.Many2one('sale.order', store=False)
    order_id = fields.Many2one('order.management', string='Order', store=False)
    order_document_no = fields.Char(string="Document No", readonly=True, copy=False, default=_get_next_order_no)
    order_date_ordered = fields.Date(string='Order Date', default=get_default_current_date)
    order_date_shipment = fields.Date(string='Shipment Date', default=get_default_current_date)
    order_business_partner = fields.Many2one('res.partner', 'Customer')
    order_partner_name = fields.Char('name')
    order_bussiness_partner_name_2 = fields.Char('名称2')
    order_address_1 = fields.Char('address 1')
    order_address_2 = fields.Char('address 2')
    order_address_3 = fields.Char('address 3')
    order_summary = fields.Text('摘要')
    order_userinput_id = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.uid,
                                         domain=_get_domain_x_userinput_id)
    sales_rep = fields.Many2one('hr.employee', string='Sales Rep')
    related_sales_rep_name = fields.Char('Sales rep name', related='sales_rep.name')
    order_payment_terms_custom = fields.Many2one('account.payment.term')
    customer_trans_classification_code = fields.Selection([('sale', '掛売'), ('cash', '現金'), ('account', '諸口')],
                                                          string='Transaction Class', default='sale')
    tax_method = fields.Selection([
        ('foreign_tax', '外税／明細'),
        ('internal_tax', '内税／明細'),
        ('voucher', '伝票'),
        ('invoice', '請求'),
        ('custom_tax', '税調整別途')
    ], string='Tax Transfer', default='foreign_tax')
    order_date_printed = fields.Date(string='Date Printed', default=get_default_current_date)
    order_payment_rule_1 = fields.Selection([('rule_cash', 'Cash'), ('rule_check', 'Check'),
                                             ('rule_credit', 'Credit Card'), ('rule_direct_debit', 'Direct Debit'),
                                             ('rule_deposit', 'Direct Deposit'), ('rule_on_credit', 'On Credit')],
                                            'payment rule', default='rule_on_credit')
    ref = fields.Char(string='Ref')
    customer_closing_date = fields.Many2one(string='Closing Date',
                                            related='order_business_partner.customer_closing_date')
    order_summary = fields.Text('摘要')
    customer_tax_rounding = fields.Selection(
        [('round', 'Rounding'), ('roundup', 'Round Up'), ('rounddown', 'Round Down')],
        string='Tax Rounding', default='round')
    order_calendar = fields.Selection([('japan', '和暦'), ('origin', '西暦')], string='Calendar', default='japan')
    is_print_date = fields.Boolean(string='Print Date', default=True)
    order_bussiness_partner_name_2 = fields.Char('名称2')
    order_customer_code_for_search = fields.Char('Customer Code', related='order_business_partner.customer_code')
    customer_office = fields.Char('Customer Office', compute='get_office')
    customer_group = fields.Char('Customer Group')
    customer_state = fields.Char('Customer State')
    customer_industry = fields.Char('Customer Industry')
    partner_id = fields.Many2one('res.partner', string='Business Partner')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If you change the pricelist, only newly added lines will be affected.", default=1)
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True,
                                  required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     tracking=5)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    flag_history = fields.Integer(string='flag_history', default=0, compute='_check_flag_history')
    order_line = fields.One2many('order.management.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    copy_history_item = fields.Char(default="")
    copy_history_from = fields.Char(default="")

    arr_changed = []

    @api.onchange('refer_quotation_history')
    def _onchange_refer_quotation_history(self):
        for rec in self:
            if rec.refer_quotation_history:
                rec.flag_history = 1
        if self.refer_quotation_history:
            data = self.refer_quotation_history
            self.order_business_partner = data.partner_id
            self.changed_fields_order_management.append('order_business_partner')
            self.order_partner_name = data.partner_name
            self.order_bussiness_partner_name_2 = data.partner_name_2
            self.order_summary = data.note
            self.customer_closing_date = data.partner_id.customer_closing_date
            self.is_print_date = data.is_print_date
            self.tax_method = data.tax_method
            self.order_calendar = data.quotation_calendar
            self.sales_rep = data.cb_partner_sales_rep_id

            lines = []

            for line in data.order_line.sorted(key=lambda i: i.quotation_custom_line_no):
                lines.append((0, 0, {
                    'class_item': line.class_item,
                    'product_id': line.product_id,
                    'product_code': line.product_code,
                    'product_barcode': line.product_barcode,
                    'product_name': line.product_name,
                    'product_name2': line.product_name2,
                    'product_uom_id': line.product_uom_id,
                    'product_standard_number': line.product_standard_number,
                    'product_maker_name': line.product_maker_name,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'line_amount': line.line_amount,
                    'tax_id': line.tax_id,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount,
                    'description': line.description,
                    'price_include_tax': line.price_include_tax,
                    'price_no_tax': line.price_no_tax,
                    'quotation_custom_line_no': line.quotation_custom_line_no
                }))

            self.order_line = lines

    @api.onchange('order_business_partner', 'order_partner_name', 'ref', 'order_bussiness_partner_name_2',
                  'order_address_1', 'order_address_2', 'order_address_3', 'order_summary', 'sales_rep')
    def _check_flag_history(self):
        for rec in self:
            if rec.order_partner_name or rec.order_business_partner or rec.ref or rec.order_bussiness_partner_name_2 or rec.order_address_1 \
                    or rec.order_address_2 or rec.order_address_3 or rec.order_summary or rec.sales_rep:
                rec.flag_history = 1
            else:
                rec.flag_history = 0

    @api.onchange('order_id')
    def _onchange_order_id(self):
        for rec in self:
            if rec.order_id:
                rec.flag_history = 1
        self.set_order(self.order_id.id)
        
    changed_fields_order_management = []

    @api.model
    def set_order(self, order_id):
        # TODO set order
        order_management = self.env['order.management'].browse(order_id)

        if order_management:
            self.ref = order_management.ref
            self.order_business_partner = order_management.order_business_partner
            self.changed_fields_order_management.append('order_business_partner')
            self.order_partner_name = order_management.order_partner_name
            self.order_bussiness_partner_name_2 = order_management.order_bussiness_partner_name_2
            self.order_address_1 = order_management.order_address_1
            self.order_address_2 = order_management.order_address_2
            self.sales_rep = order_management.sales_rep
            self.order_payment_rule_1 = order_management.order_payment_rule_1
            self.order_payment_terms_custom = order_management.order_payment_terms_custom
            self.customer_group = order_management.customer_group
            self.customer_state = order_management.customer_state
            self.customer_industry = order_management.customer_industry
            self.customer_trans_classification_code = order_management.customer_trans_classification_code
            self.order_summary = order_management.order_summary
            self.order_userinput_id = order_management.order_userinput_id
            self.customer_closing_date = order_management.customer_closing_date
            self.tax_method = order_management.tax_method
            self.order_date_shipment = order_management.order_date_shipment
            self.order_date_printed = order_management.order_date_printed
            self.is_print_date = order_management.is_print_date
            self.order_calendar = order_management.order_calendar
            order_lines = []
            for line in order_management[0].order_line.sorted(key='quotation_custom_line_no'):
                copied_data = line.copy_data()[0]
                copied_data['quotation_custom_line_no'] = line.quotation_custom_line_no
                order_lines += [[0, 0, copied_data]]
            # default['order_line'] = [(0, 0, line) for line in lines if line]
            self.order_line = order_lines

    @api.onchange('order_business_partner')
    def _onchange_business_partner(self):
        if 'order_business_partner' not in self.changed_fields_order_management and self.order_business_partner:
            for record in self:
                record.order_business_partner = self.order_business_partner
                record.order_partner_name = self.order_business_partner.name
                record.order_address_1 = self.order_business_partner.street
                record.order_address_2 = self.order_business_partner.street2
                record.sales_rep = self.order_business_partner.customer_agent
                record.order_payment_rule_1 = self.order_business_partner.payment_rule
                record.order_payment_terms_custom = self.order_business_partner.payment_terms
                record.order_bussiness_partner_name_2 = self.order_business_partner.customer_name_2
                record.customer_group = self.order_business_partner.customer_supplier_group_code.name
                record.customer_state = self.order_business_partner.customer_state.name
                record.customer_industry = self.order_business_partner.customer_industry_code.name
                record.customer_trans_classification_code = self.order_business_partner.customer_trans_classification_code
        else:
            self.changed_fields_order_management = []

    @api.onchange('copy_history_item')
    def copy_from_history(self):
        if not self.copy_history_item:
            return
        products = []
        invoice_line_ids = []
        if self.copy_history_from == 'order.management.line' and self.copy_history_item:
            products = self.env["order.management.line"].search([('id', 'in', self.copy_history_item.split(','))])
            for line in products:
                self.order_line = [(0, False, {
                    'class_item': line.class_item,
                    'product_id': line.product_id,
                    'product_code': line.product_code,
                    'product_barcode': line.product_barcode,
                    'product_name': line.product_name,
                    'product_name2': line.product_name2,
                    'product_standard_number': line.product_standard_number,
                    'product_maker_name': line.product_maker_name,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'product_uom_id': line.product_uom_id,
                    'line_amount': line.line_amount,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount,
                    'price_include_tax': line.price_include_tax,
                    'price_no_tax': line.price_no_tax,
                    'description': line.description,
                    'quotation_custom_line_no': len(self.order_line) + 1,
                    'copy_history_flag': True,
                })]
        elif self.copy_history_from == 'sale.order.line' and self.copy_history_item:
            products = self.env["sale.order.line"].search([('id', 'in', self.copy_history_item.split(','))])
            for line in products:
                self.order_line = [(0, False, {
                    'class_item': line.class_item,
                    'product_id': line.product_id,
                    'product_code': line.product_code,
                    'product_barcode': line.product_barcode,
                    'product_name': line.product_name,
                    'product_name2': line.product_name2,
                    'product_standard_number': line.product_standard_number,
                    'product_maker_name': line.product_maker_name,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'product_uom_id': line.product_uom_id,
                    'line_amount': line.line_amount,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount,
                    'price_include_tax': line.price_include_tax,
                    'price_no_tax': line.price_no_tax,
                    'description': line.description,
                    'quotation_custom_line_no': len(self.order_line) + 1,
                    'copy_history_flag': True,
                })]
        elif self.copy_history_from == 'account.move.line' and self.copy_history_item:
            products = self.env["account.move.line"].search([('id', 'in', self.copy_history_item.split(','))])
            for line in products:
                self.order_line = [(0, False, {
                    'class_item': line.x_invoicelinetype,
                    'product_id': line.product_id,
                    'product_code': line.product_code,
                    'product_barcode': line.product_barcode,
                    'product_name': line.product_name,
                    'product_name2': line.product_name2,
                    'product_standard_number': line.invoice_custom_standardnumber,
                    'product_maker_name': line.product_maker_name,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'product_uom_id': line.product_uom_id,
                    'line_amount': line.invoice_custom_lineamount,
                    'tax_rate': line.tax_rate,
                    'line_tax_amount': line.line_tax_amount,
                    'price_include_tax': line.price_include_tax,
                    'price_no_tax': line.price_no_tax,
                    'description': line.invoice_custom_Description,
                    'quotation_custom_line_no': len(self.order_line) + 1,
                    'copy_history_flag': True,
                })]
        elif self.copy_history_from == 'product.product':
            product_ids = [int(product_id) for product_id in
                           self.copy_history_item.split(',')]
            products = self.env["product.product"].browse(product_ids)
            line_vals = []
            for i, product in enumerate(products, 1):
                line_vals += \
                    [(0, False,
                      {'product_id': product.id,
                       'product_code': product.product_code,
                       'product_barcode': product.barcode,
                       'product_name': product.name,
                       'product_name2': product.product_custom_goodsnamef,
                       'product_standard_number':
                           product.product_custom_standardnumber,
                       'product_maker_name': product.product_maker_name,
                       'product_uom': product.uom_id.id,
                       'product_uom_id': product.product_uom_custom,
                       'cost': product.cost,
                       'product_standard_price': product.standard_price or 0.00,
                       'tax_rate': product.product_tax_rate,
                       'quotation_custom_line_no': len(self.order_line) + i})]
            self.order_line = line_vals
            for line in self.order_line:
                if line.product_code:
                    line._onchange_product_code()
                elif line.product_barcode:
                    line._onchange_product_barcode()
                # line.compute_price_unit()
        elif self.copy_history_from == 'duplicated':
            self.order_line = [(0, False, {
                'class_item': self.order_line[int(self.copy_history_item)].class_item,
                'product_id': self.order_line[int(self.copy_history_item)].product_id.id,
                'product_code': self.order_line[int(self.copy_history_item)].product_code,
                'product_barcode': self.order_line[int(self.copy_history_item)].product_barcode,
                'product_name': self.order_line[int(self.copy_history_item)].product_name,
                'product_name2': self.order_line[int(self.copy_history_item)].product_name2,
                'product_standard_number': self.order_line[int(self.copy_history_item)].product_standard_number,
                'product_maker_name': self.order_line[int(self.copy_history_item)].product_maker_name,
                'product_uom_qty': self.order_line[int(self.copy_history_item)].product_uom_qty,
                'price_unit': self.order_line[int(self.copy_history_item)].price_unit,
                'product_uom_id': self.order_line[int(self.copy_history_item)].product_uom_id,
                'line_amount': self.order_line[int(self.copy_history_item)].line_amount,
                'tax_rate': self.order_line[int(self.copy_history_item)].tax_rate,
                'line_tax_amount': self.order_line[int(self.copy_history_item)].line_tax_amount,
                'price_include_tax': self.order_line[int(self.copy_history_item)].price_include_tax,
                'price_no_tax': self.order_line[int(self.copy_history_item)].price_no_tax,
                'description': self.order_line[int(self.copy_history_item)].description,
                'quotation_custom_line_no': len(self.order_line) + 1,
                'copy_history_flag': self.order_line[int(self.copy_history_item)].copy_history_flag,
            })]
        self.copy_history_item = ''

    def _check_data(self, values):
        if values.get('order_document_no'):
            sale_order_count = self.env['order.management'].search_count(
                [('order_document_no', '=', values.get('order_document_no'))])
            if sale_order_count > 0:
                raise ValidationError(_('The Document No has already been registered'))

        return True

    @api.model
    def create(self, values):
        if not values.get('order_line', []):
            raise UserError(_("You need to add a line before save."))
        self._cr.execute('''
                           SELECT order_document_no
                           FROM order_management
                           WHERE SUBSTRING(order_document_no, 5) ~ '^[0-9\.]+$';
                       ''')
        query_res = self._cr.fetchall()

        if values.get('order_document_no'):
            seq = values['order_document_no']
        else:
            seq = self.env['ir.sequence'].next_by_code('order.management')
        # if new document no. already exits, do again
        while seq in [res[0] for res in query_res]:
            seq = self.env['ir.sequence'].next_by_code('order.management')

        values['order_document_no'] = seq

        self._check_data(values)
        # TODO set report header
        if 'report_header' in values:
            self.env.company.report_header = values.get('report_header')
            # self.env.company.report_header = dict(self._fields['report_header'].selection).get(
            #     values.get('report_header'))
        else:
            self.env.company.report_header = ''

        order_management = super(OrderManagement, self).create(values)

        return order_management

    def get_office(self):
        for rec in self:
            temp = ''
            partner = rec.order_business_partner
            for line in partner.relation_id:
                if line.relate_related_partner.name:
                    temp = line.relate_related_partner.name
                    # break
            rec.customer_office = temp

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                if line.class_item != 'サンプル':
                    if order.tax_method != 'custom_tax':
                        if order.tax_method == 'voucher' and line.product_id.product_tax_category == 'foreign':
                            # total_line_tax = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())
                            line_tax_amount = (line.tax_rate * line.price_unit * line.product_uom_qty) / 100
                            amount_tax += line_tax_amount
                        else:
                            amount_tax += line.line_tax_amount
                    else:
                        amount_tax = order.amount_tax

                    amount_untaxed += line.line_amount
                # amount_tax += line.line_tax_amount

            if order.tax_method == 'voucher':
                amount_tax = rounding(amount_tax, 0, order.customer_tax_rounding)

            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.onchange('amount_tax')
    def _onchange_amount_tax(self):
        for order in self:
            amount_untaxed = 0.0
            for line in order.order_line:
                if line.class_item != 'サンプル':
                    amount_untaxed += line.line_amount
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_total': amount_untaxed + self.amount_tax,
            })

    def action_paid(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.order_business_partner not in order.message_partner_ids):
            order.message_subscribe([order.order_business_partner.id])
        self.write({
            'state': 'paid',
            'order_date_ordered': fields.Datetime.now()
        })
        self._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True

    def _action_confirm(self):
        """ Implementation of additionnal mecanism of Sales Order confirmation.
            This method should be extended when the confirmation should generated
            other documents. In this method, the SO are in 'sale' state (not yet 'done').
        """
        # create an analytic account if at least an expense product
        for order in self:
            if any([expense_policy not in [False, 'no'] for expense_policy in order.order_line.mapped('product_id.expense_policy')]):
                if not order.analytic_account_id:
                    order._create_analytic_account()
        return True

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_done(self):
        for order in self:
            tx = order.sudo().transaction_ids.get_last_transaction()
            if tx and tx.state == 'pending' and tx.acquirer_id.provider == 'transfer':
                tx._set_transaction_done()
                tx.write({'is_processed': True})
        return self.write({'state': 'done'})

    def _get_forbidden_state_confirm(self):
        return {'done', 'cancel'}

    def _create_analytic_account(self, prefix=None):
        for order in self:
            analytic = self.env['account.analytic.account'].create(order._prepare_analytic_account_data(prefix))
            order.analytic_account_id = analytic

    def _prepare_analytic_account_data(self, prefix=None):
        name = self.name
        if prefix:
            name = prefix + ": " + self.name
        return {
            'name': name,
            'code': self.client_order_ref,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id
        }

    def get_lines(self):
        records = self.env['order.management.line'].search([
            ('order_id', 'in', self._ids)
        ], order='quotation_custom_line_no').read()

        for record in records:
            if record['tax_id']:
                self._cr.execute('''
                                    SELECT id, name
                                    FROM account_tax
                                    WHERE id IN %s
                                ''', [tuple(record['tax_id'])])
                query_res = self._cr.fetchall()
                record['tax_id'] = ', '.join([str(res[1]) for res in query_res])

            if record['display_type']:
                record['class_item'] = record['name']
                record['name'] = ''

        return {
            'template': 'order_lines',
            'records': records
        }

    @api.constrains('order_date_ordered', 'order_line', 'order_partner_name', 'order_document_no')
    def _change_date_invoiced(self):
        for line in self.order_line:
            line.order_date_ordered = self.order_date_ordered
            line.partner_id = self.order_business_partner
            line.document_no = self.order_document_no
            line.customer_name = self.order_partner_name

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context.copy()
        domain = []
        if ctx.get('have_advance_search'):
            check = 0
            arr = ["order_customer_code_for_search", "order_partner_name", "related_sales_rep_name"]
            for se in args:
                if se[0] == '&':
                    continue
                if se[0] == 'search_category' and se[2] == 'equal':
                    check = 1
                if check == 1 and se[0] in arr:
                    se[1] = '=ilike'
                if se[0] != 'search_category':
                    domain += [se]
                if se[0] == 'order_document_no':
                    string_middle = ''
                    if len(se[2]) < 7:
                        for i in range(6 - len(se[2])):
                            string_middle += '0'
                        string_middle = '1' + string_middle
                    if len(se[2]) < 11:
                        se[2] = ''.join(["ARO-", string_middle, se[2]])
            args = domain
        res = super(OrderManagement, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res


class OrderManagementLine(models.Model):
    _name = "order.management.line"

    order_id = fields.Many2one('order.management', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', default=None)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    tax_rate = fields.Float('Tax Rate')
    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)
    product_uom_qty = fields.Float(string='Product UOM Qty', digits=(12, 0), default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    price_unit = fields.Float(string='Price Unit', digits='Product Price', compute="compute_price_unit", store="True")
    partner_id = fields.Many2one('res.partner', string='Business Partner')
    customer_name = fields.Char(string="Customer Name")
    document_no = fields.Char(string='Document No')
    partner_id = fields.Many2one('res.partner', string='Business Partner')
    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id'], store=True, string='Currency',
                                  readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True, index=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    description = fields.Text(string='Description')
    class_item = fields.Selection([
        ('通常', '通常'),
        ('返品', '返品'),
        ('値引', '値引'),
        ('サンプル', 'サンプル')
    ], string='Class Item', default='通常')

    product_code = fields.Char(string='Product Code')
    product_barcode = fields.Char(string='Product Barcode')
    product_maker_name = fields.Char(string='Freight Category')
    product_name = fields.Text(string='Product Name')
    product_name2 = fields.Text(string='Product Name 2')
    product_standard_number = fields.Char(string='Product Standard Number')
    product_standard_price = fields.Float(string='Product List Price')
    cost = fields.Float(string='Cost')
    line_amount = fields.Float('Line Amount', compute='compute_line_amount')

    line_tax_amount = fields.Float('Tax Amount', compute='compute_line_tax_amount')

    # Reference to open dialog
    refer_detail_history = fields.Many2one('order.management.line', store=False)

    price_no_tax = fields.Float('Price No Tax')
    price_include_tax = fields.Float('Price Include Tax')
    product_tax_category = fields.Selection(
        related="product_id.product_tax_category"
    )
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id'], store=True, string='Currency',
                                  readonly=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_custom_attribute_value_ids = fields.One2many('product.attribute.custom.value', 'sale_order_line_id',
                                                         string="Custom Values")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
    ], related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')
    sequence = fields.Integer(string='Sequence', default=10)
    copy_history_flag = fields.Boolean(default=False, store=False)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    @api.onchange('quotation_custom_line_no', 'class_item', 'product_code', 'product_barcode', 'product_maker_name',
                  'product_name', 'product_standard_number', 'product_uom_qty', 'product_uom_id', 'price_unit',
                  'tax_rate')
    def change_tax_rounding(self):
        self.ensure_one()
        self.order_id.customer_tax_rounding = self.order_id.partner_id.customer_tax_rounding

    def price_of_recruitment_select(self, rate=0, recruitment_price_select=None, price_applied=0):
        if recruitment_price_select:
            product_price_ids = self.env['product.product'].search([('barcode', '=', self.product_barcode)])
            if recruitment_price_select == 'price_1':
                price = product_price_ids.price_1 * rate / 100
            elif recruitment_price_select == 'standard_price':
                price = product_price_ids.standard_price * rate / 100
        else:
            price = price_applied
        return price

    def set_country_state_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                               product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                               maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                               industry_code=None, country_state_code=None, date=datetime.today()):
        country_state_code_ids = self.env['master.price.list'].search([
            ('country_state_code_id', '=', country_state_code),
            ('industry_code_id', '=', industry_code),
            ('supplier_group_code_id', '=', supplier_group_code),
            ('customer_code_bill', '=', customer_code_bill),
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(country_state_code_ids):
            if len(country_state_code_ids) > 1:
                for i in country_state_code_ids:
                    price = self.price_of_recruitment_select(i.rate,
                                                             i.recruitment_price_select,
                                                             i.price_applied)
            else:
                price = self.price_of_recruitment_select(country_state_code_ids.rate,
                                                         country_state_code_ids.recruitment_price_select,
                                                         country_state_code_ids.price_applied)
        else:
            country_state_code_id_none = self.env['master.price.list'].search([
                ('country_state_code_id', '=', None),
                ('industry_code_id', '=', industry_code),
                ('supplier_group_code_id', '=', supplier_group_code),
                ('customer_code_bill', '=', customer_code_bill),
                ('customer_code', '=', customer_code),
                ('maker_code', '=', maker),
                ('product_class_code_lv1_id', '=', product_class_code_lv1),
                ('product_class_code_lv2_id', '=', product_class_code_lv2),
                ('product_class_code_lv3_id', '=', product_class_code_lv3),
                ('product_class_code_lv4_id', '=', product_class_code_lv4),
                ('jan_code', '=', jan_code),
                ('product_code', '=', product_code),
                ('date_applied', '<=', date)]).sorted('date_applied')
            if len(country_state_code_id_none):
                if len(country_state_code_id_none) > 1:
                    for i in country_state_code_id_none:
                        price = self.price_of_recruitment_select(i.rate, i.recruitment_price_select, i.price_applied)
                else:
                    price = self.price_of_recruitment_select(country_state_code_id_none.rate,
                                                             country_state_code_id_none.recruitment_price_select,
                                                             country_state_code_id_none.price_applied)
            else:
                product_price_ids = self.env['product.product'].search([('barcode', '=', self.product_barcode)])
                price = product_price_ids.price_1
        return price

    def set_industry_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                          product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                          maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                          industry_code=None, country_state_code=None, date=datetime.today()):
        industry_code_ids = self.env['master.price.list'].search([
            ('industry_code_id', '=', industry_code),
            ('supplier_group_code_id', '=', supplier_group_code),
            ('customer_code_bill', '=', customer_code_bill),
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(industry_code_ids):
            if len(industry_code_ids) > 1:
                price = self.set_country_state_code(product_code, jan_code, product_class_code_lv4,
                                                    product_class_code_lv3, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(industry_code_ids.rate,
                                                         industry_code_ids.recruitment_price_select,
                                                         industry_code_ids.price_applied)
        else:
            price = self.set_country_state_code(product_code, jan_code, product_class_code_lv4, product_class_code_lv3,
                                                product_class_code_lv2, product_class_code_lv1, maker, None, None, None,
                                                None, country_state_code, date)
        return price

    def set_supplier_group_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                                maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                                industry_code=None, country_state_code=None, date=datetime.today()):
        supplier_group_code_ids = self.env['master.price.list'].search([
            ('supplier_group_code_id', '=', supplier_group_code),
            ('customer_code_bill', '=', customer_code_bill),
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(supplier_group_code_ids):
            if len(supplier_group_code_ids) > 1:
                price = self.set_industry_code(product_code, jan_code, product_class_code_lv4, product_class_code_lv3,
                                               product_class_code_lv2, product_class_code_lv1, maker, customer_code,
                                               customer_code_bill, supplier_group_code, industry_code,
                                               country_state_code, date)
            else:
                price = self.price_of_recruitment_select(supplier_group_code_ids.rate,
                                                         supplier_group_code_ids.recruitment_price_select,
                                                         supplier_group_code_ids.price_applied)
        else:
            price = self.set_industry_code(product_code, jan_code, product_class_code_lv4, product_class_code_lv3,
                                           product_class_code_lv2, product_class_code_lv1, maker, None, None, None,
                                           industry_code, country_state_code, date)
        return price

    def set_customer_code_bill(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                               product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                               maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                               industry_code=None, country_state_code=None, date=datetime.today()):
        customer_code_bill_ids = self.env['master.price.list'].search([
            ('customer_code_bill', '=', customer_code_bill),
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(customer_code_bill_ids):
            if len(customer_code_bill_ids) > 1:
                price = self.set_supplier_group_code(product_code, jan_code, product_class_code_lv4,
                                                     product_class_code_lv3, product_class_code_lv2,
                                                     product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                     supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(customer_code_bill_ids.rate,
                                                         customer_code_bill_ids.recruitment_price_select,
                                                         customer_code_bill_ids.price_applied)
        else:
            price = self.set_supplier_group_code(product_code, jan_code, product_class_code_lv4,
                                                 product_class_code_lv3, product_class_code_lv2,
                                                 product_class_code_lv1, maker, None, None,
                                                 supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_customer_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                          product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                          maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                          industry_code=None, country_state_code=None, date=datetime.today()):
        customer_code_ids = self.env['master.price.list'].search([
            ('customer_code', '=', customer_code),
            ('maker_code', '=', maker),
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(customer_code_ids):
            if len(customer_code_ids) > 1:
                price = self.set_customer_code_bill(product_code, jan_code, product_class_code_lv4,
                                                    product_class_code_lv3, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(customer_code_ids.rate,
                                                         customer_code_ids.recruitment_price_select,
                                                         customer_code_ids.price_applied)
        else:
            price = self.set_customer_code_bill(product_code, jan_code, product_class_code_lv4,
                                                product_class_code_lv3, product_class_code_lv2,
                                                product_class_code_lv1, maker, None, customer_code_bill,
                                                supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_maker(self, product_code=None, jan_code=None, product_class_code_lv4=None, product_class_code_lv3=None,
                  product_class_code_lv2=None, product_class_code_lv1=None, maker=None, customer_code=None,
                  customer_code_bill=None, supplier_group_code=None, industry_code=None, country_state_code=None,
                  date=datetime.today()):
        maker_ids = self.env['master.price.list'].search([('maker_code', '=', maker),
                                                          ('product_class_code_lv1_id', '=', product_class_code_lv1),
                                                          ('product_class_code_lv2_id', '=', product_class_code_lv2),
                                                          ('product_class_code_lv3_id', '=', product_class_code_lv3),
                                                          ('product_class_code_lv4_id', '=', product_class_code_lv4),
                                                          ('jan_code', '=', jan_code),
                                                          ('product_code', '=', product_code),
                                                          ('date_applied', '<=', date)]).sorted('date_applied')
        if len(maker_ids):
            if len(maker_ids) > 1:
                price = self.set_customer_code(product_code, jan_code, product_class_code_lv4,
                                               product_class_code_lv3, product_class_code_lv2,
                                               product_class_code_lv1, maker, customer_code, customer_code_bill,
                                               supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(maker_ids.rate,
                                                         maker_ids.recruitment_price_select,
                                                         maker_ids.price_applied)
        else:
            product_price_ids = self.env['product.product'].search([('barcode', '=', self.product_barcode)])
            if product_price_ids.price_1:
                price = product_price_ids.price_1
            else:
                price = product_price_ids.standard_price
        return price

    def set_product_class_code_lv1(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                   product_class_code_lv3=None, product_class_code_lv2=None,
                                   product_class_code_lv1=None, maker=None, customer_code=None, customer_code_bill=None,
                                   supplier_group_code=None, industry_code=None, country_state_code=None,
                                   date=datetime.today()):
        product_class_code_lv1_ids = self.env['master.price.list'].search([
            ('product_class_code_lv1_id', '=', product_class_code_lv1),
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_class_code_lv1_ids):
            if len(product_class_code_lv1_ids) > 1:
                price = self.set_maker(product_code, jan_code, product_class_code_lv4,
                                       product_class_code_lv3, product_class_code_lv2,
                                       product_class_code_lv1, maker, customer_code,
                                       customer_code_bill,
                                       supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_class_code_lv1_ids.rate,
                                                         product_class_code_lv1_ids.recruitment_price_select,
                                                         product_class_code_lv1_ids.price_applied)
        else:
            price = self.set_maker(None, None, None, None, None, None, maker, customer_code, customer_code_bill,
                                   supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_product_class_code_lv2(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                   product_class_code_lv3=None, product_class_code_lv2=None,
                                   product_class_code_lv1=None, maker=None, customer_code=None, customer_code_bill=None,
                                   supplier_group_code=None, industry_code=None, country_state_code=None,
                                   date=datetime.today()):
        product_class_code_lv2_ids = self.env['master.price.list'].search([
            ('product_class_code_lv2_id', '=', product_class_code_lv2),
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_class_code_lv2_ids):
            if len(product_class_code_lv2_ids) > 1:
                price = self.set_product_class_code_lv1(product_code, jan_code, product_class_code_lv4,
                                                        product_class_code_lv3, product_class_code_lv2,
                                                        product_class_code_lv1, maker, customer_code,
                                                        customer_code_bill,
                                                        supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_class_code_lv2_ids.rate,
                                                         product_class_code_lv2_ids.recruitment_price_select,
                                                         product_class_code_lv2_ids.price_applied)
        else:
            price = self.set_product_class_code_lv1(None, None, None, None, None,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_product_class_code_lv3(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                   product_class_code_lv3=None, product_class_code_lv2=None,
                                   product_class_code_lv1=None, maker=None, customer_code=None, customer_code_bill=None,
                                   supplier_group_code=None, industry_code=None, country_state_code=None,
                                   date=datetime.today()):
        product_class_code_lv3_ids = self.env['master.price.list'].search([
            ('product_class_code_lv3_id', '=', product_class_code_lv3),
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_class_code_lv3_ids):
            if len(product_class_code_lv3_ids) > 1:
                price = self.set_product_class_code_lv2(product_code, jan_code, product_class_code_lv4,
                                                        product_class_code_lv3, product_class_code_lv2,
                                                        product_class_code_lv1, maker, customer_code,
                                                        customer_code_bill,
                                                        supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_class_code_lv3_ids.rate,
                                                         product_class_code_lv3_ids.recruitment_price_select,
                                                         product_class_code_lv3_ids.price_applied)
        else:
            price = self.set_product_class_code_lv2(None, None, None,
                                                    None, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_product_class_code_lv4(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                                   product_class_code_lv3=None, product_class_code_lv2=None,
                                   product_class_code_lv1=None, maker=None, customer_code=None, customer_code_bill=None,
                                   supplier_group_code=None, industry_code=None, country_state_code=None,
                                   date=datetime.today()):
        product_class_code_lv4_ids = self.env['master.price.list'].search([
            ('product_class_code_lv4_id', '=', product_class_code_lv4),
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_class_code_lv4_ids):
            if len(product_class_code_lv4_ids) > 1:
                price = self.set_product_class_code_lv3(product_code, jan_code, product_class_code_lv4,
                                                        product_class_code_lv3, product_class_code_lv2,
                                                        product_class_code_lv1, maker, customer_code,
                                                        customer_code_bill,
                                                        supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_class_code_lv4_ids.rate,
                                                         product_class_code_lv4_ids.recruitment_price_select,
                                                         product_class_code_lv4_ids.price_applied)
        else:
            price = self.set_product_class_code_lv3(None, None, None,
                                                    product_class_code_lv3, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_price_by_jan_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                              product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                              maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                              industry_code=None, country_state_code=None, date=datetime.today()):
        jan_ids = self.env['master.price.list'].search([
            ('jan_code', '=', jan_code),
            ('product_code', '=', product_code),
            ('date_applied', '<=', date)]).sorted('date_applied')
        if len(jan_ids):
            if len(jan_ids) > 1:
                price = self.set_product_class_code_lv4(product_code, jan_code, product_class_code_lv4,
                                                        product_class_code_lv3, product_class_code_lv2,
                                                        product_class_code_lv1, maker, customer_code,
                                                        customer_code_bill,
                                                        supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(jan_ids.rate,
                                                         jan_ids.recruitment_price_select,
                                                         jan_ids.price_applied)
        else:
            price = self.set_product_class_code_lv4(None, None, product_class_code_lv4,
                                                    product_class_code_lv3, product_class_code_lv2,
                                                    product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                    supplier_group_code, industry_code, country_state_code, date)
        return price

    def set_price_product_code(self, product_code=None, jan_code=None, product_class_code_lv4=None,
                               product_class_code_lv3=None, product_class_code_lv2=None, product_class_code_lv1=None,
                               maker=None, customer_code=None, customer_code_bill=None, supplier_group_code=None,
                               industry_code=None, country_state_code=None, date=datetime.today()):
        product_code_ids = self.env['master.price.list'].search(
            [('product_code', '=', product_code), ('date_applied', '<=', date)]).sorted('date_applied')
        if len(product_code_ids):
            if len(product_code_ids) > 1:
                price = self.set_price_by_jan_code(product_code, jan_code, product_class_code_lv4,
                                                   product_class_code_lv3, product_class_code_lv2,
                                                   product_class_code_lv1, maker, customer_code, customer_code_bill,
                                                   supplier_group_code, industry_code, country_state_code, date)
            else:
                price = self.price_of_recruitment_select(product_code_ids.rate,
                                                         product_code_ids.recruitment_price_select,
                                                         product_code_ids.price_applied)
        else:
            price = self.set_price_by_jan_code(None, jan_code, product_class_code_lv4, product_class_code_lv3,
                                               product_class_code_lv2, product_class_code_lv1, maker, customer_code,
                                               customer_code_bill, supplier_group_code, industry_code,
                                               country_state_code, date)
        return price

    def _get_default_line_no(self):
        context = dict(self._context or {})
        line_ids = context.get('default_line_ids')
        order_id = context.get('default_order_id')
        # max1 = 0

        list_line = []
        if order_id:
            list_line = self.env["order.management.line"].search([("order_id.id", "=", order_id)])

        # get all line in db and state draf
        list_final = {}
        if list_line is not None:
            for l_db in list_line:
                list_final[l_db.id] = l_db.quotation_custom_line_no
            if line_ids is not None:
                for l_v in line_ids:
                    # check state (delete,update,new,no change)
                    # 0: new
                    # 1: update
                    # 2: delete
                    # 4: no change
                    if l_v[0] == 0:
                        list_final[l_v[1]] = l_v[2]['quotation_custom_line_no']
                    if l_v[0] == 1 and 'quotation_custom_line_no' in l_v[2]:
                        list_final[l_v[1]] = l_v[2]['quotation_custom_line_no']
                    if l_v[0] == 2:
                        list_final[l_v[1]] = 0
        max = 0
        for id in list_final:
            if max < list_final[id]:
                max = list_final[id]
        return max + 1

    quotation_custom_line_no = fields.Integer('Line No', default=_get_default_line_no)
    product_uom_id = fields.Char(string='UoM')
    changed_fields = []

    @api.onchange('product_code')
    def _onchange_product_code(self):
        if 'product_code' not in self.changed_fields:
            if self.product_code:
                product = self.env['product.product'].search([
                    '|', '|', '|', '|', '|',
                    ['product_code_1', '=', self.product_code],
                    ['product_code_2', '=', self.product_code],
                    ['product_code_3', '=', self.product_code],
                    ['product_code_4', '=', self.product_code],
                    ['product_code_5', '=', self.product_code],
                    ['product_code_6', '=', self.product_code]
                ])
                if len(product) == 1:
                    self.changed_fields.append('product_barcode')
                    self.product_id = product.id
                    self.product_barcode = product.barcode

                    setting_price = "1"
                    if self.product_code == product.product_code_2:
                        setting_price = "2"
                    elif self.product_code == product.product_code_3:
                        setting_price = "3"
                    elif self.product_code == product.product_code_4:
                        setting_price = "4"
                    elif self.product_code == product.product_code_5:
                        setting_price = "5"
                    elif self.product_code == product.product_code_6:
                        setting_price = "6"
                    if product.product_tax_category == 'exempt':
                        self.price_include_tax = self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered)
                    elif product.product_tax_category == 'foreign':
                        self.price_include_tax = (product.product_tax_rate / 100 + 1) * self.set_price_product_code(
                            self.product_code, self.product_barcode, product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id, product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id, product.product_maker_code,
                            self.order_id.partner_id.customer_code, self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered)
                        self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered)
                    else:
                        self.price_include_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode, product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id, product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id, product.product_maker_code,
                            self.order_id.partner_id.customer_code, self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered)
                        self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id,
                            self.order_id.order_date_ordered) / (product.product_tax_rate / 100 + 1)

                    self.compute_price_unit()
                    self.compute_line_amount()
                    self.compute_line_tax_amount()
                    return
            # else
            self.product_barcode = ''
        else:
            self.changed_fields.remove('product_code')

    @api.onchange('product_barcode')
    def _onchange_product_barcode(self):
        if 'product_barcode' not in self.changed_fields:
            if self.product_barcode:
                product = self.env['product.product'].search([
                    ['barcode', '=', self.product_barcode]
                ])
                if product:
                    self.changed_fields.append('product_code')
                    self.product_id = product.id
                    if product.product_code_1:
                        self.product_code = product.product_code_1
                    elif product.product_code_2:
                        self.product_code = product.product_code_2
                    elif product.product_code_3:
                        self.product_code = product.product_code_3
                    elif product.product_code_4:
                        self.product_code = product.product_code_4
                    elif product.product_code_5:
                        self.product_code = product.product_code_5
                    elif product.product_code_6:
                        self.product_code = product.product_code_6
                    setting_price = '1'
                    if product.setting_price:
                        setting_price = product.setting_price[5:]
                    if product.product_tax_category == 'exempt':
                        self.price_include_tax = self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered)
                    elif product.product_tax_category == 'foreign':
                        self.price_include_tax = (product.product_tax_rate / 100 + 1) * self.set_price_product_code(
                            self.product_code, self.product_barcode, product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id, product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id, product.product_maker_code,
                            self.order_id.partner_id.customer_code, self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered)
                        self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered)
                    else:
                        self.price_include_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode, product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id, product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id, product.product_maker_code,
                            self.order_id.partner_id.customer_code, self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered)
                        self.price_no_tax = self.set_price_product_code(
                            self.product_code, self.product_barcode,
                            product.product_class_code_lv4.id,
                            product.product_class_code_lv3.id,
                            product.product_class_code_lv2.id,
                            product.product_class_code_lv1.id,
                            product.product_maker_code,
                            self.order_id.partner_id.customer_code,
                            self.order_id.partner_id.customer_code_bill,
                            self.order_id.partner_id.customer_supplier_group_code.id,
                            self.order_id.partner_id.customer_industry_code.id,
                            self.order_id.partner_id.customer_state.id, self.order_id.order_date_ordered) / (
                                                    product.product_tax_rate / 100 + 1)
                    self.compute_price_unit()
                    self.compute_line_amount()
                    self.compute_line_tax_amount()
                    return

            # Else
            self.product_code = ''
        else:
            self.changed_fields.remove('product_barcode')

    @api.onchange('refer_detail_history')
    def _get_detail_history(self):
        if self.refer_detail_history:
            data = self.refer_detail_history

            if not data.display_type:
                self.changed_fields = ['product_code', 'product_barcode', 'product_id']
                self.class_item = data.class_item
                self.product_id = data.product_id
                self.product_name = data.product_name
                self.product_name2 = data.product_name2
                self.product_code = data.product_code
                self.product_barcode = data.product_barcode
                self.product_maker_name = data.product_maker_name
                self.product_standard_number = data.product_standard_number
                self.product_standard_price = data.product_standard_price
                self.product_uom_qty = data.product_uom_qty
                self.product_uom_id = data.product_uom_id
                self.price_unit = data.price_unit
                self.cost = data.cost
                self.line_amount = data.line_amount
                self.tax_rate = data.tax_rate
                self.line_tax_amount = data.line_tax_amount
                self.description = data.description

            self.name = data.name
            self.display_type = data.display_type

    @api.onchange('product_id')
    def _get_detail_product(self):
        if 'product_id' not in self.changed_fields:
            for line in self:
                if not line.product_id or line.display_type in ('line_section', 'line_note'):
                    line.product_id = ''
                    line.product_name = ''
                    line.product_name2 = ''
                    line.product_uom_id = ''
                    line.product_maker_name = ''
                    line.product_standard_number = ''
                    line.product_standard_price = 0
                    line.cost = 0
                    line.tax_rate = 0
                    continue

                line.product_id = line.product_id or ''
                line.product_name = line.product_id.name or ''
                line.product_name2 = line.product_id.product_custom_goodsnamef or ''
                line.product_uom_id = line.product_id.product_uom_custom or ''
                line.product_maker_name = line.product_id.product_maker_name or ''
                line.product_standard_number = line.product_id.product_custom_standardnumber or ''
                line.product_standard_price = line.product_id.standard_price or 0.00
                line.cost = line.product_id.cost or 0.00
                line.tax_rate = line.product_id.product_tax_rate or 0.00

    @api.onchange('class_item')
    def _onchange_class_item(self):
        for line in self:
            if line.class_item == 'サンプル':
                # Check product sample
                sample_product_ids = self.env['product.product'].search([('barcode', '=', '0000000000000')])
                if sample_product_ids:
                    line.product_id = sample_product_ids
                else:
                    raise ValidationError(
                        _('Must create a sample product in the product master\n- JANコード: 0000000000000'))

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'order_id.tax_method',
                 'order_id.customer_tax_rounding', 'class_item', 'tax_rate')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=None)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

            if line.class_item == '通常':
                if line.product_uom_qty < 0:
                    line.product_uom_qty = line.product_uom_qty * (-1)
            elif line.class_item in ('返品', '値引'):
                if line.product_uom_qty > 0:
                    line.product_uom_qty = line.product_uom_qty * (-1)
            elif line.class_item == 'サンプル':
                line.product_uom_qty = 0
                line.price_unit = 0
                line.tax_rate = 0
                line.product_maker_name = ''
                line.product_standard_number = ''
                line.description = ''
                line.product_uom_id = ''

            line.compute_price_unit()
            line.compute_line_amount()
            line.compute_line_tax_amount()

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        for line in self:
            exchange_rate = 1
            # TH - code
            if line.product_id.product_tax_category == 'foreign':
                if line.order_id.partner_id.customer_apply_rate == "customer":
                    if line.order_id.partner_id.customer_rate and line.order_id.partner_id.customer_rate > 0:
                        exchange_rate = line.order_id.partner_id.customer_rate / 100
                elif line.order_id.partner_id.customer_apply_rate == "category":
                    if line.product_id.product_class_code_lv4 \
                            and line.product_id.product_class_code_lv4.product_class_rate \
                            and line.product_id.product_class_code_lv4.product_class_rate > 0:
                        exchange_rate = line.product_id.product_class_code_lv4.product_class_rate / 100

                if line.product_id.product_tax_category == 'exempt':
                    line.price_no_tax = line.price_include_tax = line.price_unit / exchange_rate
                else:
                    if line.order_id.tax_method == 'internal_tax':
                        line.price_include_tax = line.price_unit / exchange_rate
                        line.price_no_tax = line.price_unit / (line.tax_rate / 100 + 1) / exchange_rate
                    elif line.order_id.tax_method == 'custom_tax':
                        if line.product_id.product_tax_category == 'foreign':
                            line.price_no_tax = line.price_unit / exchange_rate
                            line.price_include_tax = line.price_unit * (line.tax_rate / 100 + 1) / exchange_rate
                        elif line.product_id.product_tax_category == 'internal':
                            line.price_include_tax = line.price_unit / exchange_rate
                            line.price_no_tax = line.price_unit / (line.tax_rate / 100 + 1) / exchange_rate
                        else:
                            line.price_no_tax = line.price_include_tax = line.price_unit / exchange_rate
                    else:
                        line.price_no_tax = line.price_unit / exchange_rate
                        line.price_include_tax = line.price_unit * (line.tax_rate / 100 + 1) / exchange_rate
            elif line.product_id.product_tax_category == 'internal':
                line.price_include_tax = line.price_unit / exchange_rate
                line.price_no_tax = line.price_unit / (line.tax_rate / 100 + 1) / exchange_rate
            else:
                line.price_no_tax = line.price_include_tax = line.price_unit / exchange_rate
            # TH - done

    @api.depends('order_id.tax_method')
    def compute_price_unit(self):
        for line in self:
            # todo set price follow product code
            # TH - code
            if line.product_id.product_tax_category == 'foreign':
                if line.order_id.tax_method == 'internal_tax':
                    price_unit = line.price_include_tax
                elif line.order_id.tax_method == 'custom_tax':
                    if line.product_id.product_tax_category == 'foreign':
                        price_unit = line.price_no_tax
                    elif line.product_id.product_tax_category == 'internal':
                        price_unit = line.price_include_tax
                    else:
                        price_unit = line.price_no_tax
                else:
                    price_unit = line.price_no_tax

                if line.order_id.partner_id.customer_apply_rate == "customer":
                    if line.order_id.partner_id.customer_rate and line.order_id.partner_id.customer_rate > 0:
                        price_unit = price_unit * line.order_id.partner_id.customer_rate / 100
                elif line.order_id.partner_id.customer_apply_rate == "category":
                    if line.product_id.product_class_code_lv4 \
                            and line.product_id.product_class_code_lv4.product_class_rate \
                            and line.product_id.product_class_code_lv4.product_class_rate > 0:
                        price_unit = price_unit * line.product_id.product_class_code_lv4.product_class_rate / 100
            elif line.product_id.product_tax_category == 'internal':
                price_unit = line.price_include_tax
            else:
                price_unit = line.price_no_tax
            # TH - done
            if line.copy_history_flag:
                price_unit = line.price_unit
            if line.class_item == 'サンプル':
                line.price_unit = 0
            else:
                line.price_unit = price_unit

    def compute_line_amount(self):
        for line in self:
            line.line_amount = self.get_compute_line_amount(line.price_unit, line.discount, line.product_uom_qty,
                                                            line.order_id.customer_tax_rounding)

    def get_compute_line_amount(self, price_unit=0, discount=0, quantity=0, line_rounding='round'):
        result = price_unit * quantity - (discount * price_unit / 100) * quantity
        return rounding(result, 0, line_rounding)

    def compute_line_tax_amount(self):
        for line in self:
            # TH - code
            if line.product_id.product_tax_category == 'foreign':
                if (line.order_id.tax_method == 'foreign_tax'
                    and line.product_id.product_tax_category != 'exempt') \
                        or (line.order_id.tax_method == 'custom_tax'
                            and line.product_id.product_tax_category == 'foreign'):
                    # total_line_tax = sum(tax.amount for tax in line.tax_id._origin.flatten_taxes_hierarchy())
                    line.line_tax_amount = self.get_compute_line_tax_amount(line.line_amount,
                                                                            line.tax_rate,
                                                                            line.order_id.customer_tax_rounding,
                                                                            line.class_item)
                else:
                    line.line_tax_amount = 0
            else:
                line.line_tax_amount = 0
            # TH - done
            line._onchange_price_unit()

    # Set tax for tax_method = voucher
    voucher_line_tax_amount = fields.Float('Voucher Line Tax Amount', compute='set_voucher_line_tax_amount', default=0)

    def set_voucher_line_tax_amount(self):
        for re in self:
            if (re.order_id.tax_method == 'voucher'
                    and re.product_id.product_tax_category != 'exempt'):
                re.voucher_line_tax_amount = (re.line_amount * re.tax_rate) / 100
            else:
                re.voucher_line_tax_amount = 0

    def get_compute_line_tax_amount(self, line_amount, line_taxes, line_rounding, line_type):
        if line_amount != 0:
            return rounding(line_amount * line_taxes / 100, 0, line_rounding)
        else:
            return 0


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context.copy()
        if ctx.get('have_advance_search'):
            domain = []
            check = 0
            arr = ["partner_id", "partner_id.name", "order_id.sales_rep", "product_code", "product_barcode",
                   "product_standard_number", "product_maker_name", "product_name"]
            for se in args:
                if se[0] == '&':
                    continue
                if se[0] == 'search_category' and se[2] == 'equal':
                    check = 1
                if check == 1 and se[0] in arr:
                    se[1] = '=ilike'
                if se[0] != 'search_category':
                    domain += [se]
                # TH - custom domain
                if se[0] == 'document_no':
                    string_middle = ''
                    if len(se[2]) < 7:
                        for i in range(6 - len(se[2])):
                            string_middle += '0'
                        string_middle = '1' + string_middle
                    if len(se[2]) < 11:
                        se[2] = ''.join(["ARO-", string_middle, se[2]])
                # TH - done
            args = domain
        res = super(OrderManagementLine, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res
