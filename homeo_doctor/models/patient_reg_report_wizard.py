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
        patient_list = []
        sl = 1
        for patient in patients:
            patient_list.append({
                'sl': sl,
                'reference_no': patient.reference_no,
                'patient_name': patient.patient_id,
                'age': patient.age,
                'address': patient.address,
                'phone': patient.phone_number,
                'doctor': patient.doc_name if patient.doc_name else '',
            })
            sl += 1

        data = {
            'form': {
                'from_date': self.from_date,
                'to_date': self.to_date,
                'patients': patient_list,
            }
        }
        print(patient_list,'patient_listpatient_listpatient_listpatient_listpatient_listpatient_listpatient_listpatient_listpatient_listpatient_list')

        return self.env.ref('homeo_doctor.action_patient_registration_pdf').report_action(self, data=data)

    def action_export_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_patient_excel?from_date=%s&to_date=%s' % (self.from_date, self.to_date),
            'target': 'new',
        }