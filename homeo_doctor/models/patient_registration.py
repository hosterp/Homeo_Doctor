from datetime import date

import dateutil.utils
from odoo import api, fields, models, tools,_
import odoo.addons
# from datetime import datetime, date
# default=date.today()
class PatientRegistration(models.Model):
    _name = 'patient.reg'
    _description = 'Patient Registration'
    _rec_name = 'reference_no'
    _order = 'reference_no desc'

    reference_no = fields.Char(string="Reference")
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date')
    patient_id = fields.Char(required=True, string="Name")
    address = fields.Text(required=True, string="Address")
    age = fields.Integer(string="Age" , compute='_compute_age', store=True)
    phone_number = fields.Char(string="Mobile No",size=12)
    email = fields.Char(string="Email ID")
    pin_code = fields.Integer(string="PIN Code")
    id_proof = fields.Binary(string='Upload ID Proof')
    echs_id = fields.Char(string="ECHS ID")
    department_id=fields.Many2one('doctor.department',string='Department',required=True)
    doc_name=fields.Many2one('doctor.profile',string='Doctor',required=True)
    registration_fee = fields.Float(string="Registration Fee", required=True, default=50.0)
    remark = fields.Text(string="Remark")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", required=True)
    lab_report_count = fields.Integer(string="Lab Reports", compute='_compute_lab_report_count')
    time=fields.Datetime(string="Date & Time")
    mri_report_ids = fields.One2many('scanning.mri', 'patient_id', string="MRI Reports")
    ct_report_ids = fields.One2many('scanning.ct', 'patient_id', string="CT Reports")
    xray_report_ids = fields.One2many('scanning.x.ray', 'patient_id', string="X-Ray Reports")
    audiology_report_ids = fields.One2many('audiology.ref', 'patient_id', string="Audiology")
    consultation_fee = fields.Integer(string='Consultation Fee', compute='_compute_consultation_fee', store=True)
    # prescription_line_ids = fields.One2many('pharmacy.prescription.line', 'admission_id', string="Prescriptions")
    lab_report_reg_ids = fields.One2many('doctor.lab.report', 'user_ide', string="Lab")
    mri_report_reg_ids = fields.One2many('scanning.mri', 'user_ide', string="MRI")
    ct_report_reg_ids = fields.One2many('scanning.ct', 'user_ide', string="CT")
    audiology_report_reg_ids = fields.One2many('audiology.ref', 'user_ide', string="Audiology")
    xray_report_reg_ids = fields.One2many('audiology.ref', 'user_ide', string="X Ray")

    bystander_name = fields.Char(string="Bystander Name")
    bystander_mobile = fields.Char(string="Bystander Mobile No")
    bystander_relation = fields.Char(string="Relation")
    bystander_email = fields.Char(string="Email ID")
    room_category = fields.Many2one('room.category', string='Room Category')
    advance_amount = fields.Integer(string='Per Day')
    bed_number = fields.Integer(string='Bed Number')
    nurse_charge = fields.Integer(string='Nurse Fee')
    alternate_no = fields.Char(string='Alternate Number')
    no_days = fields.Integer(string='Number Of Days',compute='_compute_no_days', store=True)
    admitted_date = fields.Datetime(string='Admitted Date')
    admission_boolean=fields.Boolean(default=False)
    dob = fields.Date(string='DOB' ,required=True)
    discharge_date=fields.Datetime(string='Discharge Date')

    def action_report_patient_card(self):
        return self.env.ref('homeo_doctor.report_patient_card').report_action(self)

    @api.depends('discharge_date')
    def _compute_no_days(self):
        for record in self:
            if record.admitted_date:
                admitted_date = fields.Datetime.from_string(record.admitted_date)
                current_date =record.discharge_date
                record.no_days = (current_date - admitted_date).days + 1
            else:
                record.no_days = 0

    @api.onchange('no_days')
    def _admission_button_active(self):
        vals=self.env['patient.registration'].search([('patient_id', '=', self.reference_no)])
        vals.move_to_admission_clicked=False


    @api.depends('dob')
    def _compute_age(self):
        for record in self:
            if record.dob:
                today = date.today()
                dob = record.dob

                record.age = today.year - dob.year - (
                        (today.month, today.day) < (dob.month, dob.day)
                )
            else:
                record.age = 0
    @api.onchange('room_category')
    def onchange_advance_amount(self):
        for i in self:
            if i.room_category:
                i.advance_amount = i.room_category.advance_amount
                i.nurse_charge = i.room_category.nursing_fee

            else:
                pass
    @api.depends('doc_name')
    def _compute_consultation_fee(self):
        for record in self:
            if record.doc_name:
                # Automatically populate consultation_fee from the selected doctor's record
                record.consultation_fee = record.doc_name.consultation_fee_doctor



    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            return {
                'domain': {
                    'doc_name': [('department_id', '=', self.department_id.id)],
                }
            }
        return {
            'domain': {
                'doc_name': []
            }
        }

    def _compute_lab_report_count(self):
        for record in self:
            # Count the lab reports for this patient
            record.lab_report_count = self.env['doctor.lab.report'].search_count([('patient_id', '=', record.id)])

    def action_view_lab_reports(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Reports',
            'res_model': 'doctor.lab.report',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': dict(self.env.context, default_patient_id=self.id),
        }

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'patient.reg.group') or _('New')
        record = super(PatientRegistration, self).create(vals)

        self.env['patient.registration'].create({
            'user_id': record.id,
            'patient_id': record.patient_id,
            'address': record.address,
            'age': record.age,
            'phone_number': record.phone_number,
            'doctor_id': record.doc_name,
            'appointment_date' : record.time,
        })

        return record

    def _compute_formatted_date(self):
        for record in self:
            if record.date:
                formatted_date = record.date.strftime('%d/%m/%Y')
                record.formatted_date = formatted_date
            else:
                record.formatted_date = ''

    @api.model
    def search_patient_by_phone(self, phone_number):
        return self.search([('phone_number', 'ilike', phone_number)])

    def action_create_appointment(self):
        appointment_vals = {
            'patient_id': self.id,
            'appointment_date': fields.Datetime.now(),
            'doctor_id': self.doc_name.id,
            'department': self.department_id.id,
            'status': 'draft',
        }
        appointment = self.env['patient.appointment'].create(appointment_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Patient Appointment',
            'res_model': 'patient.appointment',
            'view_mode': 'form',
            'res_id': appointment.id,
            'target': 'current',
        }


class RoomCategory(models.Model):
    _name = 'room.category'
    _rec_name = 'room_category'

    room_category=fields.Char(string='Room Category')
    advance_amount=fields.Integer(string='Advance Amount')
    nursing_fee=fields.Integer(string='Nursing Fee')





