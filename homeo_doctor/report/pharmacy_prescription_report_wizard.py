from odoo import models, fields, api

class PharmacyPrescriptionReportWizard(models.TransientModel):
    _name = 'pharmacy.prescription.report.wizard'
    _description = 'Pharmacy Prescription Report Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    medicine_id = fields.Many2one('product.product', string='Medicine')

    def print_report(self):
        self.ensure_one()

        domain = [
            ('pharmacy_id.date', '>=', self.date_from),
            ('pharmacy_id.date', '<=', self.date_to),
        ]
        if self.medicine_id:
            domain.append(('product_id', '=', self.medicine_id.id))  # Use correct field name

        # Make sure this is correct model: pharmacy.prescription.line
        lines = self.env['pharmacy.prescription.line'].search(domain)

        # ✅ Pass actual line records
        return self.env.ref('homeo_doctor.report_pharmacy_prescription').report_action(lines)



