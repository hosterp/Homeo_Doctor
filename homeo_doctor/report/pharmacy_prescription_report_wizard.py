from odoo import models, fields, api

class PharmacyPrescriptionReportWizard(models.TransientModel):
    _name = 'pharmacy.prescription.report.wizard'
    _description = 'Pharmacy Prescription Report Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    medicine_id = fields.Many2one('product.product', string='Medicine')
    with_patient_name = fields.Boolean(string="Include Patient Name", default=False)

    # def print_report(self):
    #     self.ensure_one()
    #
    #     domain = [
    #         ('pharmacy_id.date', '>=', self.date_from),
    #         ('pharmacy_id.date', '<=', self.date_to),
    #     ]
    #     if self.medicine_id:
    #         domain.append(('product_id', '=', self.medicine_id.id))
    #
    #
    #     lines = self.env['pharmacy.prescription.line'].search(domain)
    #
    #     return self.env.ref('homeo_doctor.report_pharmacy_prescription').report_action(lines)
    def print_report(self):
        self.ensure_one()
        return self.env.ref('homeo_doctor.report_pharmacy_prescription').report_action(self)

    def _get_prescription_lines(self):
        domain = [
            ('pharmacy_id.date', '>=', self.date_from),
            ('pharmacy_id.date', '<=', self.date_to),
        ]
        if self.medicine_id:
            domain.append(('product_id', '=', self.medicine_id.id))
        return self.env['pharmacy.prescription.line'].search(domain)


