from email.policy import default

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

    reference_no = fields.Char(string="Reference")
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date')
    user_id = fields.Many2one('patient.reg', string='Name',required=True)
    patient_id = fields.Char(string='Patient ID',required=True,related='user_id.reference_no')
    patient_name = fields.Char(string='Name',required=True,related='user_id.patient_id')
    doctor_id=fields.Char(string='Doctor name')
    address = fields.Text(string='Address',required=True,related='user_id.address')
    age = fields.Integer( string='Age',required=True,related='user_id.age')
    phone_number = fields.Char( string='Phone No',size=12,related='user_id.phone_number')
    gender = fields.Selection( string='Gender',related='user_id.gender')
    symptoms = fields.Text(string="Symptoms")
    professional_diagnosis = fields.Text(string='Professional Diagnosis')
    remark = fields.Text(string="Remark")
    checkup_reports=fields.Text(string='Checkup Details')
    med_ids = fields.One2many("prescription.entry.lines", 'prescription_line_id', string="Prescription Entry Lines")
    lab_report_count = fields.Integer(string="Lab Reports", compute='_compute_lab_report_count')
    move_to_pharmacy_clicked = fields.Boolean(string="Move to Pharmacy Clicked", default=False)
    move_to_admission_clicked = fields.Boolean(string="Move to Patient Reg  Clicked", default=False)
    blood_pressure = fields.Char(string='Blood Pressure')
    blood_pressure_low = fields.Char(string='Blood Pressure')
    sugar_level = fields.Integer(string='Sugar Level (mg/dl)')
    ppbs = fields.Integer(string='PPBS (mg/dl)')
    weight = fields.Float(string='Weight (kg)')
    mri_report_ids = fields.One2many('scanning.mri', 'patient_id', string="MRI")
    ct_report_ids = fields.One2many('scanning.ct', 'patient_id', string="CT")
    xray_report_ids = fields.One2many('scanning.x.ray', 'patient_id', string="X-Ray")
    lab_report_ids = fields.One2many('doctor.lab.report', 'patient_id', string="Lab")
    audiology_report_ids = fields.One2many('audiology.ref', 'patient_id', string="Audiology")
    temperature=fields.Char(string='Temperature')
    medicine_course=fields.Char(string='medicine course')
    appointment_date =  fields.Date('Appointment Date')
    doctor_remark_ids = fields.One2many('consultation.remark', 'consultation_id', string='Doctor Remarks')
    previous_consultation_ids = fields.One2many(
        'patient.registration', 'id',
        string='Previous Consultations',
        compute='_compute_previous_consultations',
        store=False
    )

    referred_doctor_ids = fields.Many2many(
        'doctor.profile',
        # 'doctor_consultation_referred_rel',
        # 'consultation_id',
        # 'doctor_id',
        string='Referred Doctors',
    )
    referred_department_ids = fields.Many2many(
        'doctor.department',
        # 'doctor_consultation_referred_rel',
        # 'consultation_id',
        # 'doctor_id',
        string='Referred Department',
    )
    remark_boolean=fields.Boolean(default=False)
    @api.onchange('referred_doctor_ids')
    def _onchange_referred_doctor_ids(self):
        if self.referred_doctor_ids:
            self.remark_boolean=True
            existing_doctors = self.doctor_remark_ids.mapped('doctor_id')
            new_remark_lines = [(0, 0, {'doctor_id': doctor.id}) for doctor in self.referred_doctor_ids if
                                doctor not in existing_doctors]

            if new_remark_lines:
                self.doctor_remark_ids = [(5,)] + new_remark_lines
        else:
            self.remark_boolean = False


    @api.onchange('referred_department_ids')
    def _onchange_referred_department_ids(self):
        if self.referred_department_ids:
            return {
                'domain': {
                    'referred_doctor_ids': [
                        ('department_id', 'in', self.referred_department_ids.ids)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'referred_doctor_ids': []
                }
            }


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
        print("val",res)
        return res

    def _compute_formatted_date(self):
        for record in self:
            if record.date:
                formatted_date = record.date.strftime('%d/%m/%Y')
                record.formatted_date = formatted_date
            else:
                record.formatted_date = ''

    def admission_button(self):
        self.move_to_admission_clicked = True

        # Prepare admission values for prescription lines
        # admission_vals = {
        #     'prescription_line_ids': [(0, 0, {
        #         'product_id': line.product_id.id,
        #         'total_med': line.total_med,
        #         'per_ped': line.per_ped,
        #         'morn': line.morn,
        #         'noon': line.noon,
        #         'night': line.night,
        #     }) for line in self.med_ids],
        # }
        # result = {
        #     'lab_report_reg_ids': [(0, 0, {
        #         'report_details': line.report_details,
        #         'date': line.date,
        #         'doctor_id': line.doctor_id.id,
        #         'patient_id': line.patient_id.id,
        #
        #     }) for line in self.lab_report_ids],
        # }
        # mri_result = {
        #     'mri_report_reg_ids': [(0, 0, {
        #         'report_details': line.report_details,
        #         'date': line.date,
        #         'doctor_id': line.doctor_id.id,
        #         'patient_id': line.patient_id.id,
        #
        #     }) for line in self.mri_report_ids],
        # }
        # ct_result = {
        #     'ct_report_reg_ids': [(0, 0, {
        #         'report_details': line.report_details,
        #         'date': line.date,
        #         'doctor_id': line.doctor_id.id,
        #         'patient_id': line.patient_id.id,
        #
        #     }) for line in self.ct_report_ids],
        # }


        admission_record = self.env['patient.reg'].search([('reference_no', '=', self.patient_id)], limit=1)
        # lab_record = self.env['patient.reg'].search([('reference_no', '=', self.patient_id)], limit=1)
        # mri_record = self.env['patient.reg'].search([('reference_no', '=', self.patient_id)], limit=1)
        # ct_record = self.env['patient.reg'].search([('reference_no', '=', self.patient_id)], limit=1)
        admission_record.admission_boolean=True
        # if admission_record:

            # for line_vals in admission_vals['prescription_line_ids']:
            #     admission_record.prescription_line_ids = [(0, 0, line_vals[2])]
        # if lab_record:
        #     for line_vals in result['lab_report_reg_ids']:
        #         lab_record.lab_report_reg_ids = [(0, 0, line_vals[2])]
        # if mri_record:
        #     for line_vals in mri_result['mri_report_reg_ids']:
        #         mri_record.mri_report_reg_ids = [(0, 0, line_vals[2])]
        # if ct_record:
        #     for line_vals in ct_result['ct_report_reg_ids']:
        #         ct_record.ct_report_reg_ids = [(0, 0, line_vals[2])]
        # else:

            # admission_record = self.env['patient.reg'].create(admission_vals)

        # Notify the user about the success
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Record updated or created successfully!',
                'sticky': False,
                'warning': False,
            }
        }

    def action_move_to_pharmacy(self):
        self.move_to_pharmacy_clicked = True
        pharmacy_vals = {
            'name': self.patient_name,
            'patient_id': self.patient_id,
            'phone_number': self.phone_number,
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

    def action_create_referral_xray(self,scan_type='xray'):
        for consultation in self:
            if not consultation.user_id:  # Assuming user_id is the patient
                raise UserError("Patient not selected.")

            # Debugging output
            print("User  ID:", consultation.user_id)
            print("User  Reference No:", consultation.user_id.reference_no)

            # Create the referral record
            referral = self.env['doctor.referral'].create({
                'doctor_id': consultation.doctor_id.id,
                'user_ide': consultation.user_id.id,
                'patient_id': consultation.reference_no,
                'patient_name': consultation.patient_name,
                'referral_type': 'scanning',
                'details': f'Refer for {scan_type.replace("_", " ").title()}',
                'scan_type': scan_type,
            })

            # Create the xray scan record and link it to the reference_no
            x_ray_vals = {
                'patient_id': consultation.user_id.id,
                'doctor_id': consultation.doctor_id.id,
                'reference_no': consultation.reference_no,  # Ensure this is the correct reference_no
                'scan_registered_date': fields.Date.today(),
                # Add other necessary fields...
            }

            # Debugging output for xray scan values
            print("MRI Scan Values:", x_ray_vals)

            # Create the xray scan record
            xray_scan = self.env['scanning.x.ray'].create(x_ray_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Referral',
            'res_model': 'doctor.referral',
            'view_mode': 'form',
            'res_id': referral.id,
            'target': 'new',
        }


    def action_create_referral_mri(self,scan_type='mri'):
        for consultation in self:
            if not consultation.user_id:  # Assuming user_id is the patient
                raise UserError("Patient not selected.")

            # Debugging output
            print("User  ID:", consultation.user_id)
            print("User  Reference No:", consultation.user_id.reference_no)

            # Create the referral record
            referral = self.env['doctor.referral'].create({
                'doctor_id': consultation.doctor_id.id,
                'user_ide': consultation.user_id.id,
                'patient_id': consultation.reference_no,
                'referral_type': 'scanning',
                'details': f'Refer for {scan_type.replace("_", " ").title()}',
                'scan_type': scan_type,
            })

            # Create the MRI scan record and link it to the reference_no
            mri_scan_vals = {
                'patient_id': consultation.user_id.id,
                'doctor_id': consultation.doctor_id.id,
                'reference_no': consultation.reference_no,  # Ensure this is the correct reference_no
                'scan_registered_date': fields.Date.today(),
                # Add other necessary fields...
            }

            # Debugging output for MRI scan values
            print("MRI Scan Values:", mri_scan_vals)

            # Create the MRI scan record
            mri_scan = self.env['scanning.mri'].create(mri_scan_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Referral',
            'res_model': 'doctor.referral',
            'view_mode': 'form',
            'res_id': referral.id,
            'target': 'new',
        }


    def action_create_referral_ct(self,scan_type='ct'):
        for consultation in self:
            if not consultation.user_id:  # Assuming user_id is the patient
                raise UserError("Patient not selected.")

            # Debugging output
            print("User  ID:", consultation.user_id)
            print("User  Reference No:", consultation.user_id.reference_no)

            # Create the referral record
            referral = self.env['doctor.referral'].create({
                'doctor_id': consultation.doctor_id.id,
                'user_ide': consultation.user_id.id,
                'patient_id': consultation.reference_no,
                'referral_type': 'scanning',
                'details': f'Refer for {scan_type.replace("_", " ").title()}',
                'scan_type': scan_type,
            })

            # Create the ct scan record and link it to the reference_no
            ct_vals = {
                'patient_id': consultation.user_id.id,
                'doctor_id': consultation.doctor_id.id,
                'reference_no': consultation.reference_no,  # Ensure this is the correct reference_no
                'scan_registered_date': fields.Date.today(),
                # Add other necessary fields...
            }

            # Debugging output for ct scan values
            print("ct Scan Values:", ct_vals)

            # Create the ct scan record
            ct_scan = self.env['scanning.ct'].create(ct_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Referral',
            'res_model': 'doctor.referral',
            'view_mode': 'form',
            'res_id': referral.id,
            'target': 'new',
        }

    def action_create_referral_audiology(self,scan_type='audiology'):
        for consultation in self:
            if not consultation.user_id:  # Assuming user_id is the patient
                raise UserError("Patient not selected.")

            # Debugging output
            print("User  ID:", consultation.user_id)
            print("User  Reference No:", consultation.user_id.reference_no)

            # Create the referral record
            referral = self.env['doctor.referral'].create({
                'doctor_id': consultation.doctor_id.id,
                'user_ide': consultation.user_id.id,
                'patient_id': consultation.reference_no,
                'referral_type': 'scanning',
                'details': f'Refer for {scan_type.replace("_", " ").title()}',
                'scan_type': scan_type,
            })

            # Create the ct scan record and link it to the reference_no
            audiology_vals = {
                'patient_id': consultation.user_id.id,
                'doctor_id': consultation.doctor_id.id,
                'reference_no': consultation.reference_no,  # Ensure this is the correct reference_no
                'scan_registered_date': fields.Date.today(),
                # Add other necessary fields...
            }

            # Debugging output for audiology scan values
            print("Audiology Scan Values:", audiology_vals)

            # Create the ct scan record
            audio_scan = self.env['audiology.ref'].create(audiology_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Referral',
            'res_model': 'doctor.referral',
            'view_mode': 'form',
            'res_id': referral.id,
            'target': 'new',
        }

    # def _create_referral(self, scan_type):
    #     for consultation in self:
    #         if not consultation.user_id:  # Assuming user_id is the patient
    #             raise UserError("Patient not selected.")
    #
    #         # Debugging output
    #         print("User  ID:", consultation.user_id)
    #         print("User  Reference No:", consultation.user_id.reference_no)
    #
    #         # Create the referral record
    #         referral = self.env['doctor.referral'].create({
    #             'doctor_id': consultation.doctor_id.id,
    #             'user_ide': consultation.user_id.id,
    #             'patient_id': consultation.reference_no,
    #             'referral_type': 'scanning',
    #             'details': f'Refer for {scan_type.replace("_", " ").title()}',
    #             'scan_type': scan_type,
    #         })
    #
    #         # Create the MRI scan record and link it to the reference_no
    #         mri_scan_vals = {
    #             'patient_id': consultation.user_id.id,
    #             'doctor_id': consultation.doctor_id.id,
    #             'reference_no': consultation.reference_no,  # Ensure this is the correct reference_no
    #             'scan_registered_date': fields.Date.today(),
    #             # Add other necessary fields...
    #         }
    #
    #         # Debugging output for MRI scan values
    #         print("MRI Scan Values:", mri_scan_vals)
    #
    #         # Create the MRI scan record
    #         mri_scan = self.env['scanning.mri'].create(mri_scan_vals)
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Referral',
    #         'res_model': 'doctor.referral',
    #         'view_mode': 'form',
    #         'res_id': referral.id,
    #         'target': 'new',
    #     }
    def _create_referral_lab(self):
        for consultation in self:
            if not consultation.user_id:
                raise UserError("Patient not selected.")

            # Create a lab referral record
            referral = self.env['lab.referral'].create({
                'doctor': consultation.doctor_id.id,
                'user_ide': consultation.user_id.id,
                'patient_id': consultation.reference_no,
                'patient_name': consultation.patient_name,
                'referral_type': 'lab',
            })
            if referral:
                lab_report = self.env['doctor.lab.report'].create({
                    'referral_details': referral.details,
                    'reference_no': referral.reference_no,
                    'patient_id': referral.user_ide.id,
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
            'domain': [('user_id', 'in', self.patient_id if isinstance(self.patient_id, list) else [self.patient_id])],
            'context': {'default_patient_id': self.patient_id},
        }



class PrescriptionEntryLine(models.Model):
    _name = 'prescription.entry.lines'
    _description = 'Prescription Entry Line'

    prescription_line_id = fields.Many2one("patient.registration", string="Prescription Entry")
    product_id = fields.Many2one('product.product', string="Medicine")
    total_med = fields.Integer("Tot Med")
    per_ped = fields.Integer("Per Med")
    morn = fields.Integer("Morn")
    noon = fields.Integer("Noon")
    night = fields.Integer("Night")

class DoctorReferral(models.Model):
    _name = 'doctor.referral'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string="Reference",readonly=True)
    user_ide = fields.Many2one('patient.reg', string="Patient", readonly=True)
    doctor_id = fields.Many2one('doctor.profile', string="Doctor",readonly=True)
    patient_id = fields.Many2one('patient.registration', string="Consultation ID",readonly=True)
    referral_type = fields.Selection([('scanning', 'Scanning'), ('consultation', 'Consultation')],
                                     default='scanning')
    details = fields.Text(string="Referral Details")
    scan_type = fields.Selection([('mri', 'MRI'), ('ct', 'CT Scan'), ('xray', 'X-Ray'),('audiology','Audiology')], string="Scan Type",readonly=True)
    patient_name = fields.Char(related='patient_id.patient_name', string='Patient Name')

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
    user_ide = fields.Many2one('patient.reg', string="Patient", readonly=True)
    patient_id=fields.Many2one('patient.registration',string='Patient')
    patient_name=fields.Char(related='patient_id.patient_name',string='Patient Name')
    lab_test = fields.Many2many('labtest.type', string='Lab Test')
    test_type = fields.Many2many('test.type', string='Test Type')
    referral_type = fields.Selection([('scanning', 'Scanning'), ('consultation', 'Consultation'),('lab','LAB')],
                                     default='lab')
    details = fields.Text(string="Referral Details")

    lab_report_id = fields.Many2one('doctor.lab.report', string="Lab Report", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code('lab.referral') or _('New')
        return super(LabReferral, self).create(vals)

class LabTest(models.Model):
    _name = 'labtest.type'
    _rec_name = 'lab_test'

    lab_test=fields.Char('Lab Test')


class TestType(models.Model):
    _name = 'test.type'
    _rec_name = 'test_type'

    test_type = fields.Char('Test Type')

class ConsultationRemark(models.Model):
    _name = 'consultation.remark'

    consultation_id = fields.Many2one('patient.registration', string='Consultation', ondelete='cascade')
    doctor_id = fields.Many2one('doctor.profile', string='Doctor')
    remark = fields.Text(string='Remark')