from odoo import api, fields, models, _



class Audiology(models.Model):
    _name = 'audiology.ref'
    _rec_name = 'patient_id'

    user_ide = fields.Many2one('patient.reg', string="Patient")
    patient_id = fields.Many2one('patient.registration', string="Consultation ID", required=True)
    reference_no = fields.Char(string="Reference No")
    age = fields.Integer(string='Age', required=True, related='patient_id.age')
    gender = fields.Selection(string='Gender', related='patient_id.gender')
    doctor_id = fields.Many2one('doctor.profile', string="Doctor", required=True)
    scan_registered_date = fields.Date(string="Registered Date")
    scan_report_date = fields.Date(string="Report Date")
    file_report = fields.Binary(string="Result")
    file_report_name = fields.Char(string="Result")
    investigation = fields.Text(string="Investigation")
    details = fields.Text(string="Details")
    impression = fields.Text(string="Impression")
    referral_id = fields.Many2one('doctor.referral', string="Referral ID")
    report_details = fields.Text(string="Audiology Report Details")
    therapy_line_ids = fields.One2many('audiology.therapy.line', 'audiology_id', string='Therapy Details')

    def print_invoice(self):
        return self.env.ref('homeo_doctor.action_report_audiology_invoice').report_action(self)



    def action_add_report(self, report_details):

        for scan in self:

            report = self.env['audiology.ref'].create({
                'referral_id': scan.referral_id.id,
                'patient_id': scan.patient_id.id,
                'report_details': report_details,
            })


            scan.referral_id.write({
                'ct_report_id': report.id
            })

        return True

    @api.onchange('user_ide')
    def _onchange_patient_id(self):
        if self.user_ide:
            latest_referral = self.env['doctor.referral'].search(
                [('user_ide', '=', self.user_ide.id),('scan_type','=','audiology')],
                order='create_date desc',
                limit=1
            )
            self.referral_id = latest_referral.id if latest_referral else False
            self.details = latest_referral.details if latest_referral else False
            self.patient_id = latest_referral.patient_id if latest_referral else False


class AudiologyService(models.Model):
    _name = 'audiology.service.type'
    _description = 'Type of Audiology Therapy'

    name = fields.Char(string='Service', required=True)

class Session(models.Model):
    _name = 'audiology.session'
    _description = 'Audiology Sessions'
    _rec_name = 'session'

    session = fields.Integer(string='Session', required=True)

class AudiologyRate(models.Model):
    _name = 'audiology.rate'
    _description = 'Audiology Therapy Rate'
    _rec_name = 'amount'  # This will display the amount in Many2one fields

    amount = fields.Float(string='Amount', required=True)

class AudiologyTherapyLine(models.Model):
    _name = 'audiology.therapy.line'
    _description = 'Audiology Therapy Line'

    audiology_id = fields.Many2one('audiology.ref', string='Audiology Therapy')
    service_id = fields.Many2one('audiology.service.type', string='Service', required=True)
    session_id = fields.Many2one('audiology.session', string='Session', required=True)
    rate_id = fields.Many2one('audiology.rate', string='Rate/Session', required=True)