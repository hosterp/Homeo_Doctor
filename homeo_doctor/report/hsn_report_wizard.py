from odoo import models, fields

class HSNReportWizard(models.TransientModel):
    _name = 'hsn.report.wizard'
    _description = 'HSN Report Wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)

    def print_report(self):
        return self.env.ref('homeo_doctor.action_report_hsn_gst_summary').report_action(self)