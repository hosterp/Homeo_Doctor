from odoo import api, fields, models

class PatientReportWizard(models.TransientModel):
    _name = 'patient.report.wizard'
    _description = 'Patient Report Wizard'

    date_from = fields.Date(string='From Date', required=True,default=fields.Date.today)
    date_to = fields.Date(string='To Date', required=True,default=fields.Date.today)
    doctor_id = fields.Many2one('doctor.profile', string='Doctor')
    department_id = fields.Many2one(
        'doctor.department',
        string='Department',
        related='doctor_id.department_id',
        store=True,
    )

    @api.onchange('doctor_id')
    def onchange_doctor_id(self):
        if self.doctor_id and self.doctor_id.department_id:
            return {
                'domain': {
                    'department_id': [('id', '=', self.doctor_id.department_id.id)]
                },
                'value': {
                    'department_id': self.doctor_id.department_id.id
                }
            }
        return {
            'domain': {'department_id': []},
            'value': {'department_id': False}
        }
    def action_generate_report(self):
        # Code to generate report
        report_data = self._get_report_data()  # Call a method to get the report data
        return self.env.ref('homeo_doctor.patient_pdf_report_action').report_action(self, data={
            'report_data': report_data,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })

    def _get_report_data(self):
        # Logic to get the data to be included in the report
        # This should return the report data in the format required
        patients = self.env['patient.registration'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('doctor', '=', self.doctor_id.id),

        ])
        report_data = []
        for patient in patients:
            report_data.append({
                'reference_no': patient.patient_id.display_name,
                'date': patient.appointment_date,
                'patient_name': patient.patient_name,
                'age': patient.age,
                'gender': patient.gender,
                'phone': patient.phone_number,
                'doctor_name': patient.doctor.name,
                'consultation_fee': patient.consultation_fee,
                'diagnosis': patient.professional_diagnosis,
            })
            print(report_data,'report_datareport_datareport_datareport_datareport_datareport_datareport_datareport_datareport_datareport_datareport_data')
        return report_data

    def print_excel(self):
        base_url = '/patient/excel_report'
        params = '?date_from=%s&date_to=%s&doctor_id=%s' % (
            self.date_from,
            self.date_to,
            self.doctor_id.id if self.doctor_id else ''
        )
        return {
            'type': 'ir.actions.act_url',
            'url': base_url + params,
            'target': 'new',
        }
