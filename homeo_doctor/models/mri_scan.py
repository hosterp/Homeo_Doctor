from odoo import api, fields, models, _

class MRI_Scan(models.Model):
    _name = 'scanning.mri'
    _rec_name = 'user_ide'

    user_ide = fields.Many2one('patient.reg', string="Patient")
    patient_id = fields.Many2one('patient.registration', string="Consultation ID")
    patient_name = fields.Char(related='patient_id.patient_name',string="Patient Name")
    reference_no = fields.Char(string="Reference No")
    age = fields.Integer(string='Age', related='patient_id.age')
    gender = fields.Selection(string='Gender', related='patient_id.gender')
    doctor_id = fields.Many2one('doctor.profile', string="Doctor", )
    scan_registered_date = fields.Date(string="Registered Date")
    scan_report_date = fields.Date(string="Report Date")
    file_report = fields.Binary(string="Result")
    file_report_name = fields.Char(string="Result")
    investigation = fields.Text(string="Investigation")
    details = fields.Text(string="Details")
    impression = fields.Text(string="Impression")
    referral_id = fields.Many2one('doctor.referral', string="Referral ID")
    report_details = fields.Text(string="MRI Report Details")
    scan_line_ids = fields.One2many('mri.scan.line', 'mri_id', string='Scan Lines')

    register_visible = fields.Boolean(default=True)
    register_patient_name = fields.Char("Patient Name")
    register_address = fields.Text(string="Address")
    register_age = fields.Integer(string="Age", store=True)
    register_phone_number = fields.Char(string="Mobile No", size=12)
    register_email = fields.Char(string="Email ID")
    # register_pin_code = fields.Integer(string="PIN Code")
    register_id_proof = fields.Binary(string='Upload ID Proof')
    register_vssc_id = fields.Char(string="VSSC ID No")
    # register_department_id = fields.Many2one('doctor.department', string='Department')
    # register_doc_name = fields.Many2one('doctor.profile', string='Doctor')
    registration_fee = fields.Float(string="Registration Fee", default=50.0)

    def action_walk_in_patient(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Walk-in Patients',
            'res_model': 'scanning.mri',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('homeo_doctor.view_MRI_walk_in_tree').id, 'tree'),
                      (self.env.ref('homeo_doctor.view_scanning_mri_form').id, 'form')],
            'domain': [('register_visible', '=', True)],
            'target': 'current',
        }


    @api.model
    def create(self, vals):
        # # Generate report reference if not provided
        # if vals.get('report_reference', _('New')) == _('New'):
        #     vals['report_reference'] = self.env['ir.sequence'].next_by_code('audiology.ref') or _('New')

        # Check if registration is visible and patient name is provided
        if vals.get('register_visible', True) and vals.get('register_patient_name'):
            # Prepare patient registration values
            patient_reg_vals = {
                'patient_id': vals.get('register_patient_name'),
                'address': vals.get('register_address'),
                'age': vals.get('register_age'),
                'email': vals.get('register_email'),
                'phone_number': vals.get('register_phone_number'),
                # 'registration_fee': vals.get('registration_fee', 50.0),
                'consultation_check': vals.get('consultation_check', True),
                'walk_in': True

            }
            print(patient_reg_vals)

            # Create patient registration
            self.env['patient.reg'].create(patient_reg_vals)

        return super(MRI_Scan, self).create(vals)

    def print_invoice(self):
        return self.env.ref('homeo_doctor.action_report_mri_invoice').report_action(self)

    def action_add_report(self, report_details):

        for scan in self:

            report = self.env['scanning.mri'].create({
                'referral_id': scan.referral_id.id,
                'patient_id': scan.patient_id.id,
                'report_details': report_details,
            })


            scan.referral_id.write({
                'mri_report_id': report.id
            })

        return True



    @api.onchange('user_ide')
    def _onchange_patient_id(self):
        if self.user_ide:

            latest_referral = self.env['doctor.referral'].search(
                [('user_ide', '=', self.user_ide.id),('scan_type','=','mri')],
                order='create_date desc', 
                limit=1
            )
            self.referral_id = latest_referral.id if latest_referral else False
            self.details = latest_referral.details if latest_referral else False
            self.patient_id = latest_referral.patient_id if latest_referral else False


class MRIScanType(models.Model):
    _name = 'mri.scan.type'
    _description = 'Type of MRI Scan'

    name = fields.Char(string='Scan Type', required=True)

class MRIBodyPart(models.Model):
    _name = 'mri.body.part'
    _description = 'MRI Scan Body Part'

    name = fields.Char(string='Body Part', required=True)

class MRIRate(models.Model):
    _name = 'mri.rate'
    _description = 'MRI Scan Rate'
    _rec_name = 'amount'  # This will display the amount in Many2one fields

    amount = fields.Float(string='Amount', required=True)

class MRIScanLine(models.Model):
    _name = 'mri.scan.line'
    _description = 'MRI Scan Line'

    mri_id = fields.Many2one('scanning.mri', string='MRI Scan')
    scan_type_id = fields.Many2one('mri.scan.type', string='Type of MRI Scan', required=True)
    body_part_id = fields.Many2one('mri.body.part', string='Body Part', required=True)
    rate_id = fields.Many2one('mri.rate', string='Rate', required=True)