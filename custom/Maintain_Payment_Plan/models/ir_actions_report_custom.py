from odoo import api, fields, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def render_qweb_pdf(self, res_ids=None, data=None):
        result = super(IrActionsReport, self).render_qweb_pdf(res_ids, data)
        if self.model == 'payment.plan':
            self.env['payment.plan'].browse(res_ids).write({
                'bill_report_state': True
            })
        return result
