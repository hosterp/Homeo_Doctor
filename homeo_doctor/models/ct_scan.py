from odoo import api, fields, models, _

class CT_Scan(models.Model):
    _name = 'scanning.ct'
    _rec_name = 'patient_id'

    patient_id = fields.Many2one('patient.reg', string="Patient", required=True)
    age = fields.Integer(string='Age', required=True, related='patient_id.age')
    gender = fields.Selection(string='Gender', related='patient_id.gender')
    doctor_id = fields.Many2one('doctor.profile', string="Doctor", required=True)
    scan_registered_date = fields.Date(string="Registered Date")
    scan_report_date = fields.Date(string="Report Date")
    investigation = fields.Text(string="Investigation")
    details = fields.Text(string="Details")
    impression = fields.Text(string="Impression")
    referral_id = fields.Many2one('doctor.referral', string="Referral ID")
    report_details = fields.Text(string="CT Report Details")


    def action_add_report(self, report_details):

        for scan in self:

            report = self.env['scanning.ct'].create({
                'referral_id': scan.referral_id.id,
                'patient_id': scan.patient_id.id,
                'report_details': report_details,
            })


            scan.referral_id.write({
                'ct_report_id': report.id
            })

        return True

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            latest_referral = self.env['doctor.referral'].search(
                [('patient_id', '=', self.patient_id.id),('scan_type','=','ct')],
                order='create_date desc',
                limit=1
            )
            self.referral_id = latest_referral.id if latest_referral else False
            self.details = latest_referral.details if latest_referral else False

