from odoo import models, fields

class HSNReportWizard(models.TransientModel):
    _name = 'hsn.report.wizard'
    _description = 'HSN Report Wizard'

    from_date = fields.Date(string="From Date", required=True,default=fields.Date.today)
    to_date = fields.Date(string="To Date", required=True,default=fields.Date.today)
    op_category = fields.Selection([('op', 'OP'), ('ip', 'IP'), ('others', 'OTHERS')])
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('credit', 'Credit')
    ], string='Payment Method')

    def print_report(self):
        return self.env.ref('homeo_doctor.action_report_hsn_gst_summary').report_action(self)

    def action_download_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': f"/report/excel/hsn_gst_summary?from_date={self.from_date}&to_date={self.to_date}",
            'target': 'new',
        }
