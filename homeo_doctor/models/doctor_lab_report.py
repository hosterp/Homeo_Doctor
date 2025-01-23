from odoo import api, fields, models, _

class DoctorLabReport(models.Model):
    _name = 'doctor.lab.report'
    _description = 'Doctor Lab Report'
    _rec_name = 'report_reference'
    _order = 'date desc'

    user_ide = fields.Many2one('patient.reg', string="Patient")
    patient_id = fields.Many2one('patient.registration', string="Consultation ID", required=True)
    patient_name = fields.Char(related='patient_id.patient_name',string="Patient Name")
    patient_phone = fields.Char(related='patient_id.phone_number',string="Patient Mobile Number")
    reference_no = fields.Char(string="Reference No")
    report_reference = fields.Char(string="Report Reference", readonly=True, default=lambda self: _('New'))
    date = fields.Date(string="Report Date", default=fields.Date.context_today, required=True)
    doctor_id = fields.Many2one('doctor.profile', string="Doctor", required=True)
    report_details = fields.Text(string="Report Details")
    attachment = fields.Binary(string="Result")
    attachment_name = fields.Char(string="Result")
    bill_amount=fields.Integer('Bill Amount')
    referral_id = fields.Many2one('lab.referral', string="Referral ID")
    referral_details = fields.Text(string="Referral Details")
    report_details = fields.Text(string="Lab Report Details")
    lab_reference_no=fields.Many2one('lab.referral','Reference No')
    lab_line_ids = fields.One2many('lab.scan.line', 'lab_id', string='Lab Lines')

    @api.model
    def create(self, vals):
        if vals.get('report_reference', _('New')) == _('New'):
            vals['report_reference'] = self.env['ir.sequence'].next_by_code('doctor.lab.report') or _('New')
        return super(DoctorLabReport, self).create(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(DoctorLabReport, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        if self.env.user.has_group('base.group_user'):
            doc_id = self.env['doctor.profile'].search([('user_id', '=', self.doctor_id.user_id.id)], limit=1)
            if doc_id:
                domain = [('doctor_id', '=', doc_id.id)]
                res['arch'] = res['arch'].replace('<tree', f'<tree domain="{domain}"')
        return res

    def action_add_report(self, report_details):

        for scan in self:
            report = self.env['doctor.lab.report'].create({
                'referral_id': scan.referral_id.id,
                'patient_id': scan.patient_id.id,
                'report_details': report_details,
            })

            scan.referral_id.write({
                'lab_report_id': report.id
            })

        return True

    @api.onchange('user_ide')
    def _onchange_patient_id(self):
        if self.user_ide:
            latest_referral = self.env['lab.referral'].search(
                [('user_ide', '=', self.user_ide.id)],
                order='create_date desc',
                limit=1
            )
            self.lab_reference_no = latest_referral.id if latest_referral else False
            self.referral_details=latest_referral.details if latest_referral else False
            self.patient_id = latest_referral.patient_id if latest_referral else False


    def print_invoice(self):
        return self.env.ref('homeo_doctor.action_report_ct_invoice').report_action(self)
class LabType(models.Model):
    _name = 'lab.type'
    _description = 'Type of Lab Test'

    name = fields.Char(string='Test Description', required=True)

class LabRate(models.Model):
    _name = 'lab.rate'
    _description = 'Lab Test Rate'
    _rec_name = 'amount'  # This will display the amount in Many2one fields

    amount = fields.Float(string='Amount', required=True)

class LabScanLine(models.Model):
    _name = 'lab.scan.line'
    _description = 'Lab Scan Line'

    lab_id = fields.Many2one('doctor.lab.report', string='Lab Test')
    lab_type_id = fields.Many2one('lab.type', string='Lab Test description', required=True)
    rate_id = fields.Many2one('lab.rate', string='Rate', required=True)
