import dateutil.utils
from odoo import api, fields, models, tools,_
import odoo.addons
from odoo.exceptions import UserError


# from datetime import datetime, date
# default=date.today()
class PatientRegistration(models.Model):
    _name = 'patient.registration'
    _description = 'Patient Registration'
    _rec_name = 'reference_no'
    _order = 'reference_no desc'

    reference_no = fields.Char(string="Reference",related='user_id.reference_no')
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date')
    user_id = fields.Many2one('patient.reg', string='Name',required=True)
    patient_id = fields.Char(string='Name',required=True,related='user_id.patient_id')
    doctor_id=fields.Many2one(string='Doctor name',related='user_id.doc_name')
    address = fields.Text(string='Address',required=True,related='user_id.address')
    age = fields.Integer( string='Age',required=True,related='user_id.age')
    phone_number = fields.Char( string='Phone No',size=12,related='user_id.phone_number')
    gender = fields.Selection( string='Gender',related='user_id.gender')
    symptoms = fields.Text(string="Symptoms")
    remark = fields.Text(string="Remark")
    checkup_reports=fields.Text(string='Checkup Details')
    med_ids = fields.One2many("prescription.entry.lines", 'prescription_line_id', string="Prescription Entry Lines")
    lab_report_count = fields.Integer(string="Lab Reports", compute='_compute_lab_report_count')
    move_to_pharmacy_clicked = fields.Boolean(string="Move to Pharmacy Clicked", default=False)
    blood_pressure = fields.Char(string='Blood Pressure')
    sugar_level = fields.Float(string='Sugar Level (mg/dl)')
    weight = fields.Float(string='Weight (kg)')
    mri_report_ids = fields.One2many('scanning.mri', 'patient_id', string="MRI")
    ct_report_ids = fields.One2many('scanning.ct', 'patient_id', string="CT")
    xray_report_ids = fields.One2many('scanning.x.ray', 'patient_id', string="X-Ray")
    lab_report_ids = fields.One2many('doctor.lab.report', 'patient_id', string="Lab")
    audiology_report_ids = fields.One2many('audiology.ref', 'patient_id', string="Audiology")

    previous_consultation_ids = fields.One2many(
        'patient.registration', 'id',
        string='Previous Consultations',
        compute='_compute_previous_consultations',
        store=False
    )

    @api.depends('patient_id')
    def _compute_previous_consultations(self):
        for record in self:
            # Fetch all previous consultations for the same patient, excluding the current record
            record.previous_consultation_ids = self.search([
                ('user_id', '=', record.user_id.id),
                ('id', '!=', record.id)
            ])
    def _compute_lab_report_count(self):
        for record in self:
            # Count the lab reports for this patient
            record.lab_report_count = self.env['doctor.lab.report'].search_count([('patient_id', '=', self.reference_no)])

    def action_view_lab_reports(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Reports',
            'res_model': 'doctor.lab.report',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.reference_no)],
            'context': dict(self.env.context, default_patient_id=self.reference_no),
        }
    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'patient.registrartion.group') or _('New')
        res = super(PatientRegistration, self).create(vals)
        return res

    def _compute_formatted_date(self):
        for record in self:
            if record.date:
                formatted_date = record.date.strftime('%d/%m/%Y')
                record.formatted_date = formatted_date
            else:
                record.formatted_date = ''

    def admission_button(self):

        appointment_vals = {
            'patient_id': self.id,
            'attending_doctor': self.doctor_id.id,

        }
        appointment = self.env['hospital.admitted.patient'].create(appointment_vals)
        registration_vals = {
            'user_id': self.id,
            'patient_id': self.patient_id,
            'address': self.address,
            'age': self.age,
            'phone_number': self.phone_number,
            'attending_doctor': self.doctor_id,
            'admission_date': self.formatted_date,
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Pharmacy record sent successfully!',
                'sticky': False,
                'warning': False,
            }
        }

    def action_move_to_pharmacy(self):
        self.move_to_pharmacy_clicked = True
        pharmacy_vals = {
            'name': self.patient_id,
            'patient_id': self.reference_no,
            'phone_number': self.phone_number,
            'date':self.date,
            'prescription_line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'total_med': line.total_med,
                'per_ped': line.per_ped,
                'morn': line.morn,
                'noon': line.noon,
                'night': line.night,
            }) for line in self.med_ids],
        }


        pharmacy_record = self.env['pharmacy.description'].create(pharmacy_vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Pharmacy record sent successfully!',
                'sticky': False,
                'warning': False,
            }
        }
        #
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Pharmacy Description',
        #     'res_model': 'pharmacy.description',
        #     'view_mode': 'form',
        #     'res_id': pharmacy_record.id,
        #     'target': 'current',
        # }


    def action_create_referral_lab(self):
        return self._create_referral_lab()

    def action_create_referral_ct(self):
        return self._create_referral(scan_type='ct')


    def action_create_referral_mri(self):

        return self._create_referral(scan_type='mri')


    def action_create_referral_xray(self):
        return self._create_referral(scan_type='xray')

    def action_create_referral_audiology(self):
        return self._create_referral(scan_type='audiology')

    def _create_referral(self, scan_type):
        for consultation in self:
            if not consultation.patient_id:
                raise UserError("Patient not selected.")


            referral = self.env['doctor.referral'].create({
                'doctor_id': consultation.doctor_id.id,
                'patient_id': consultation.user_id.id,
                'referral_type': 'scanning',
                'details': f'Refer for {scan_type.replace("_", " ").title()}',
                'scan_type': scan_type,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Referral',
            'res_model': 'doctor.referral',
            'view_mode': 'form',
            'res_id': referral.id,
            'target': 'new',

        }

    def _create_referral_lab(self):
        for consultation in self:
            if not consultation.patient_id:
                raise UserError("Patient not selected.")

            # Create a lab referral record
            referral = self.env['lab.referral'].create({
                'doctor': consultation.doctor_id.id,
                'patient_id': consultation.id,
                'referral_type': 'lab',
            })
            if referral:
                lab_report = self.env['doctor.lab.report'].create({
                    'referral_details': referral.details,
                    'lab_reference_no': referral.reference_no,
                    'patient_id': referral.patient_id.id,
                    'doctor_id': referral.doctor.id,

                })

            return {
                'type': 'ir.actions.act_window',
                'name': 'Lab Referral',
                'res_model': 'lab.referral',
                'view_mode': 'form',
                'res_id': referral.id,
                'target': 'new',
            }

    def action_view_consultations(self):
        test=self.env['patient.registration'].search([('patient_id', '=', [self.user_id.id])])
        print(test,'previous record..............................................')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Previous Consultations',
            'view_mode': 'tree,form',
            'res_model': 'patient.registration',
            'domain': [('user_id', 'in', self.reference_no if isinstance(self.reference_no, list) else [self.reference_no])],
            'context': {'default_patient_id': self.reference_no},
        }



class PrescriptionEntryLine(models.Model):
    _name = 'prescription.entry.lines'
    _description = 'Prescription Entry Line'

    prescription_line_id = fields.Many2one("patient.registration", string="Prescription Entry")
    product_id = fields.Many2one('product.product', string="Medicine")
    total_med = fields.Integer("Tot Med")
    per_ped = fields.Integer("Per Med")
    morn = fields.Boolean("Morn")
    noon = fields.Boolean("Noon")
    night = fields.Boolean("Night")

class DoctorReferral(models.Model):
    _name = 'doctor.referral'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string="Reference",readonly=True)
    doctor_id = fields.Many2one('doctor.profile', string="Doctor",readonly=True)
    patient_id = fields.Many2one('patient.reg', string="Patient",readonly=True)
    referral_type = fields.Selection([('scanning', 'Scanning'), ('consultation', 'Consultation')],
                                     default='scanning')
    details = fields.Text(string="Referral Details")
    scan_type = fields.Selection([('mri', 'MRI'), ('ct', 'CT Scan'), ('xray', 'X-Ray'),('audiology','Audiology')], string="Scan Type",readonly=True)


    mri_report_id = fields.Many2one('scanning.mri', string="MRI Report",readonly=True)
    ct_report_id = fields.Many2one('scanning.ct', string="CT Report",readonly=True)
    xray_report_id = fields.Many2one('scanning.x.ray', string="X-Ray Report",readonly=True)
    audiology_report_id = fields.Many2one('audiology.ref', string="Audiology Report",readonly=True)


    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'doctor.referral.group') or _('New')
        res = super(DoctorReferral, self).create(vals)
        return res

class LabReferral(models.Model):
    _name = 'lab.referral'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string="Reference", readonly=True)
    doctor=fields.Many2one('doctor.profile',string='Doctor')
    patient_id=fields.Many2one('patient.registration',string='Patient')
    referral_type = fields.Selection([('scanning', 'Scanning'), ('consultation', 'Consultation'),('lab','LAB')],
                                     default='lab')
    details = fields.Text(string="Referral Details")

    lab_report_id = fields.Many2one('doctor.lab.report', string="Lab Report", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code('lab.referral') or _('New')
        return super(LabReferral, self).create(vals)