from odoo import models, fields

class PatientRegistrationReportWizard(models.TransientModel):
    _name = 'patient.registration.report.wizard'
    _description = 'Patient Registration Report Wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)

    def action_print_pdf(self):
        patients = self.env['patient.reg'].search([
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date)
        ])
        data = {
            'patient_ids': patients.ids,
        }
        return self.env.ref('homeo_doctor.action_patient_registration_pdf').report_action(self, data=data)

    def action_export_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_patient_excel?from_date=%s&to_date=%s' % (self.from_date, self.to_date),
            'target': 'new',
        }