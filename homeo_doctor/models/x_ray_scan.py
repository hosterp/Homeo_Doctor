from odoo import api, fields, models, _

class X_RAY_Scan(models.Model):
    _name = 'scanning.x.ray'
    _rec_name = 'patient_id'

    user_ide = fields.Many2one('patient.reg', string="Patient")
    patient_id = fields.Many2one('patient.registration', string="Consultation ID", required=True)
    patient_name = fields.Char(related='patient_id.patient_name', string="Patient Name")
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
    report_details = fields.Text(string="X-RAY Report Details")
    scan_line_ids = fields.One2many('x.ray.scan.line', 'xray_id', string='Scan Lines')

    def print_invoice(self):
        return self.env.ref('homeo_doctor.action_report_xray_invoice').report_action(self)

    def action_add_report(self, report_details):
        for scan in self:
            report = self.env['scanning.x.ray'].create({
                'referral_id': scan.referral_id.id,
                'patient_id': scan.patient_id.id,
                'report_details': report_details,
            })

            scan.referral_id.write({
                'xray_report_id': report.id
            })

        return True

    @api.onchange('user_ide')
    def _onchange_patient_id(self):
        if self.user_ide:

            latest_referral = self.env['doctor.referral'].search(
                [('user_ide', '=', self.user_ide.id),('scan_type','=','xray')],
                order='create_date desc',
                limit=1
            )
            self.referral_id = latest_referral.id if latest_referral else False
            self.details = latest_referral.details if latest_referral else False
            self.patient_id = latest_referral.patient_id if latest_referral else False


class CTScanType(models.Model):
    _name = 'x.ray.scan.type'
    _description = 'Type of X-Ray Scan'

    name = fields.Char(string='Scan Type', required=True)

class CTBodyPart(models.Model):
    _name = 'x.ray.body.part'
    _description = 'X-Ray Scan Body Part'

    name = fields.Char(string='Body Part', required=True)

class CTRate(models.Model):
    _name = 'x.ray.rate'
    _description = 'X-Ray Scan Rate'
    _rec_name = 'amount'  # This will display the amount in Many2one fields

    amount = fields.Float(string='Amount', required=True)

class CTScanLine(models.Model):
    _name = 'x.ray.scan.line'
    _description = 'X-Ray Scan Line'

    xray_id = fields.Many2one('scanning.x.ray', string='X-Ray Scan')
    scan_type_id = fields.Many2one('x.ray.scan.type', string='Type of X-Ray Scan', required=True)
    body_part_id = fields.Many2one('x.ray.body.part', string='Body Part', required=True)
    rate_id = fields.Many2one('x.ray.rate', string='Rate', required=True)