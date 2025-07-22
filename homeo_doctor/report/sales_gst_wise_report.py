from odoo import models, fields, api

class PharmacyBillGSTReport(models.TransientModel):
    _name = 'pharmacy.bill.gst.report'
    _description = 'Pharmacy Bill GST Report'

    from_date = fields.Date("From Date", required=True)
    to_date = fields.Date("To Date", required=True)

    def print_report(self):
        return self.env.ref('homeo_doctor.action_report_bill_gst').report_action(self)

