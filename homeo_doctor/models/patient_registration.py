import re
from datetime import date, datetime

from gevent.util import print_run_info

from odoo.exceptions import UserError

import dateutil.utils
from odoo import api, fields, models, tools, _
import odoo.addons


# from odoo.odoo.exceptions import ValidationError


# from datetime import datetime, date
# default=date.today()
class PatientRegistration(models.Model):
    _name = 'patient.reg'
    _description = 'Patient Registration'
    _rec_name = 'reference_no'
    _order = 'reference_no desc'

    reference_no = fields.Char(string="Reference")
    token_no = fields.Char(string="Token No")
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date')
    track_registration_date = fields.Date(default=dateutil.utils.today())
    patient_id = fields.Char(string="Name")
    address = fields.Text(string="Address")
    age = fields.Integer(string="Age", store=True)
    phone_number = fields.Char(string="Mobile No", size=12)
    email = fields.Char(string="Email ID")
    pin_code = fields.Char(string="PIN Code")
    id_proof = fields.Binary(string='VSSC ID Proof')
    vssc_id = fields.Char(string="VSSC ID No")
    department_id = fields.Many2one('doctor.department', string='Department')
    doc_name = fields.Many2one('doctor.profile', string='Doctor')
    registration_fee = fields.Many2one('patient.registration.fee',string="Registration Fee", default=lambda self: self._default_registration_fee())
    remark = fields.Text(string="Remark")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    lab_report_count = fields.Integer(string="Lab Reports", compute='_compute_lab_report_count')
    time = fields.Date(string="Date & Time")
    mri_report_ids = fields.One2many('scanning.mri', 'patient_id', string="MRI Reports")
    ct_report_ids = fields.One2many('scanning.ct', 'patient_id', string="CT Reports")
    xray_report_ids = fields.One2many('scanning.x.ray', 'patient_id', string="X-Ray Reports")
    audiology_report_ids = fields.One2many('audiology.ref', 'patient_id', string="Audiology")
    consultation_fee = fields.Integer(string='Consultation Fee', compute='_compute_consultation_fee', store=True)
    # prescription_line_ids = fields.One2many('pharmacy.prescription.line', 'admission_id', string="Prescriptions")
    lab_report_reg_ids = fields.One2many('lab.result.page', 'patient_re_id_name', string="Lab")
    mri_report_reg_ids = fields.One2many('scanning.mri', 'user_ide', string="MRI")
    ct_report_reg_ids = fields.One2many('scanning.ct', 'user_ide', string="CT")
    audiology_report_reg_ids = fields.One2many('audiology.ref', 'user_ide', string="Audiology")
    xray_report_reg_ids = fields.One2many('audiology.ref', 'user_ide', string="X Ray")

    bystander_name = fields.Char(string="Bystander Name")
    bystander_mobile = fields.Char(string="Bystander Mobile No")
    bystander_relation = fields.Char(string="Relation")
    bystander_email = fields.Char(string="Email ID")
    room_category = fields.Many2one('room.category', string='Room Category')
    room_category_new = fields.Many2one('hospital.room.type', string='Room Category')
    room_id = fields.Many2one('hospital.room', string="Room")

    bed_id = fields.Many2one('hospital.bed', string="Bed",)
    advance_amount = fields.Integer(string='Per Day')
    # bed_id = fields.Many2one('hospital.bed', string='Bed')
    nurse_charge = fields.Integer(string='Nurse Fee')
    alternate_no = fields.Char(string='Alternate Number')
    no_days = fields.Integer(string='Number Of Days', compute='_compute_no_days', store=True)
    admitted_date = fields.Datetime(string='Admitted Date')
    admission_boolean = fields.Boolean(default=False)
    dob = fields.Date(string='DOB')
    discharge_date = fields.Datetime(string='Discharge Date')
    vssc_boolean = fields.Boolean(string='VSSC', default=False)
    consultation_check = fields.Boolean(default=False)
    temp_reference_no = fields.Char(string=" Temporary Reference")
    no_consultation = fields.Boolean(default=True)
    walk_in=fields.Boolean(default=False)
    op_category = fields.Many2one('op.category', string='OP Category')
    doctor = fields.Many2one('doctor.profile', string='Doctor')
    block = fields.Many2one('block',string='Block')
    new_block =fields.Many2one('hospital.block',string='Block')
    room_id = fields.Many2one('hospital.room', string="Room")
    room_number = fields.Char("Room No")
    room_transfer_date = fields.Datetime(string="Transfer Date")
    transferred_block = fields.Many2one('block',string='Block')
    transferred_room_category = fields.Many2one('room.category', string='Room Category')
    transferred_room_number = fields.Integer(string='Room No')
    transferred_bed_number = fields.Integer(string='Bed Number')
    amount_in_advance =  fields.Integer(string="Advance Amount")
    advance_mode_payment = fields.Selection([('cash', 'Cash'),
                                ('card', 'Card'),
                                ('cheque', 'Cheque'),
                                ('upi', 'Mobile Pay'),], string='Payment Method',default='cash')
    advance_remark = fields.Text(string="Remarks")
    advance_date = fields.Datetime(string="Date")
    admission_total_amount = fields.Integer(string="Total Amount")
    admission_amount_paid = fields.Integer(string="Amount Paid")
    admission_balance = fields.Integer(string="Balance")
    Staff_name = fields.Char("Staff Name")
    staff_password = fields.Char("Password")

    @api.onchange('amount_in_advance')
    def _onchage_amount_advance(self):
        for rec in self:
            rec.admission_total_amount = rec.amount_in_advance

    @api.onchange('admission_amount_paid')
    def _onchage_amount_paid(self):
        for rec in self:
            if (rec.admission_amount_paid < rec.admission_total_amount and rec.admission_amount_paid > 0):
                rec.admission_balance = rec.admission_total_amount - rec.admission_amount_paid
            elif (rec.admission_amount_paid > rec.admission_total_amount and rec.admission_amount_paid > 0):
                rec.admission_balance = rec.admission_amount_paid - rec.admission_total_amount
            else:
                rec.admission_balance = 0

    @api.depends('room_category')
    def _compute_available_room_ids(self):
        for rec in self:
            domain = [('room_type', '=', rec.room_category), ('is_available', '=', True)]
            rec.available_room_ids = self.env['hospital.room'].search(domain)

    # payment_method = fields.Selection([
    # ('cash', 'Cash'),
    # ('upi', 'UPI'),
    # ('card', 'Card')
    # ], string='Payment Method')
    # payment_reference = fields.Char(string='Payment Reference')
    status=fields.Selection([('admitted','Admitted'),('discharged','Discharged')])
    def _default_registration_fee(self):
        """Fetch the first registration fee as the default"""
        return self.env['patient.registration.fee'].search([], limit=1).id


    def action_walk_in_patient(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Walk-in Patients',
            'res_model': 'patient.reg',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('homeo_doctor.patient_reg_walk_in_tree').id, 'tree')],
            'domain': [('walk_in', '=', True)],
            'target': 'current',
        }

    def action_create_admission(self):
        admission_model = self.env['hospital.admitted.patient']
        registration_model = self.env['patient.reg']

        for rec in self:
            patient = registration_model.search([('reference_no', '=', rec.reference_no)], limit=1)
            if not patient:
                raise UserError(f"No patient found with reference no: {rec.reference_no}")

            admission_model.create({
                'patient_id': patient.id,
                'admission_date': fields.Datetime.now(),
                'room_number': rec.room_number,
                'room_category_new': rec.room_category_new.id,
                'bed_id': rec.bed_id.id,
                'attending_doctor': rec.doctor.id,
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Admission created successfully.',
                'sticky': False,
                'type': 'success',
            }
        }
    def _get_report_values(self, docids, data=None):
        docs = self.env['patient.reg'].browse(docids)
        return {
            'docs': docs,
            'company_logo': self.env.user.company_id.logo,  # Ensure logo is included
        }

    def action_register_confirm(self):
        payment_vals = {
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
        }
        for record in self:
            # Create wizard
            wizard_vals = {
                'patient_id': record.patient_id.id,
                'patient_name': record.patient_name,
                'register_id': record.id,
                'doctor_ids': [(6, 0, record.doctor_ids.ids)],
            }

            # Create wizard
            wizard = self.env['register.payment.wizard'].create(wizard_vals)

            # Create fee lines
            for doctor in record.doctor_ids:
                # Get consultation fee for this doctor
                doc_fee = 0
                for fee in record.consultation_fee_ids:
                    if fee.doctor_id.id == doctor.id:
                        doc_fee = fee.consultation_fee
                        break

                # If no fee found in consultation_fee_ids, calculate it
                if doc_fee == 0 and hasattr(doctor, 'consultation_fee_doctor'):
                    doc_fee = doctor.consultation_fee_doctor

                # Create fee line
                self.env['wizard.register.fee'].create({
                    'wizard_id': wizard.id,
                    'doctor_id': doctor.id,
                    'fee_amount': doc_fee
                })

            # Return action to open wizard
            return {
                'name': 'Register Payment',
                'type': 'ir.actions.act_window',
                'res_model': 'register.payment.wizard',
                'res_id': wizard.id,
                'view_mode': 'form',
                'target': 'new',
                'context': {'active_id': record.id}
            }

    def action_report_patient_card(self):
        return self.env.ref('homeo_doctor.report_patient_card').report_action(self)

    @api.onchange('vssc_boolean')
    def _onchange_vssc_boolean(self):
        if self.vssc_boolean:
            self.registration_fee = 0.0

    @api.depends('discharge_date')
    def _compute_no_days(self):
        for record in self:
            if record.admitted_date:
                admitted_date = fields.Datetime.from_string(record.admitted_date)
                current_date = record.discharge_date
                record.no_days = (current_date - admitted_date).days + 1
            else:
                record.no_days = 0

    @api.onchange('no_days')
    def _admission_button_active(self):
        vals = self.env['patient.registration'].search([('patient_id', '=', self.reference_no)])
        vals.move_to_admission_clicked = False

    @api.constrains('email')
    def _check_email(self):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(email_regex, record.email):
                raise UserError("⚠️ Warning: The email address '%s' is invalid." % record.email)

    @api.onchange('dob')
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

    # @api.onchange('room_category')
    # def onchange_advance_amount(self):
    #     for i in self:
    #         if i.room_category:
    #             i.advance_amount = i.room_category.advance_amount
    #             i.nurse_charge = i.room_category.nursing_fee
    #
    #         else:
    #             pass

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
        year_prefix = datetime.today().strftime("%y")  # Get last two digits of the year (e.g., "25" for 2025)

        def format_sequence(sequence):
            """Ensure sequence has at least 7 digits and prepend year prefix."""
            sequence_str = str(sequence).zfill(7)  # Ensure at least 7 digits
            return f"{year_prefix}/{sequence_str}"  # Format as "25/0012332"

        # Generate token number if doctor is selected
        if vals.get('no_consultation', False):
            vals['token_no'] = False  # Do not generate token number
            if vals.get('reference_no', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('patient.reg.group') or _('New')
                vals['reference_no'] = format_sequence(sequence)  # Apply formatting
                return super(PatientRegistration, self).create(vals)

        if vals.get('doc_name'):
            doctor = self.env['doctor.profile'].browse(vals.get('doc_name'))
            appointment_date = vals.get('time') if vals.get('time') else fields.Date.context_today(self)
            if doctor:
                vals['token_no'] = doctor.get_next_token_number(appointment_date)

        # Check if consultation_check is False before generating reference_no
        if not vals.get('consultation_check'):
            if vals.get('reference_no', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('patient.reg.group') or _('New')
                vals['reference_no'] = format_sequence(sequence)  # Apply formatting
        else:
            # If consultation_check is True, generate a temporary reference number with formatting
            if vals.get('temp_reference_no', _('New')) == _('New'):
                temp_sequence = self.env['ir.sequence'].next_by_code('patient.reg.temp') or _('New')
                vals['temp_reference_no'] = format_sequence(temp_sequence)  # Apply formatting

        # Create the main patient registration record
        record = super(PatientRegistration, self).create(vals)
        # After record creation, check if consultation_check is False
        if not vals.get('admission_boolean', False) and not record.consultation_check:
            self.env['patient.registration'].create({
                'user_id': record.id,
                'patient_id': record.id,
                'token_no': record.token_no,
                'address': record.address,
                'age': record.age,
                'phone_number': record.phone_number,
                'doctor_id': record.doc_name.display_name,
                'appointment_date': record.time,
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
    
    def open_patient_history(self):

        self.ensure_one()
        
        # Create history wizard
        history_wizard = self.env['patient.history.wizard'].create({
            'patient_id': self.id
        })
        
        # Return action to open wizard
        return {
            'name': f'Patient History - {self.patient_id}',
            'type': 'ir.actions.act_window',
            'res_model': 'patient.history.wizard',
            'res_id': history_wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }


class RoomCategory(models.Model):
    _name = 'room.category'
    _rec_name = 'room_category'

    room_category = fields.Char(string='Room Category')
    advance_amount = fields.Integer(string='Advance Amount')
    nursing_fee = fields.Integer(string='Nursing Fee')


class PatientRegistrationFee(models.Model):
    _name='patient.registration.fee'
    _rec_name='fee'

    fee=fields.Integer(string='Patient Registration Fee')




class PatientHistoryWizard(models.TransientModel):
    _name = 'patient.history.wizard'
    _description = 'Patient History Wizard'

    patient_id = fields.Many2one('patient.reg', string='Patient', required=True)
    
    # Consultation History
    consultation_history_ids = fields.One2many(
        'patient.registration', 
        compute='_compute_consultation_history', 
        string='Consultation History'
    )
    
    # Lab Reports
    lab_report_ids = fields.One2many(
        'doctor.lab.report', 
        compute='_compute_lab_reports', 
        string='Lab Reports'
    )
    
    # MRI Reports
    mri_report_ids = fields.One2many(
        'scanning.mri', 
        compute='_compute_mri_reports', 
        string='MRI Reports'
    )
    
    # CT Reports
    ct_report_ids = fields.One2many(
        'scanning.ct', 
        compute='_compute_ct_reports', 
        string='CT Reports'
    )
    
    # X-Ray Reports
    x_ray_report_ids = fields.One2many(
        'scanning.x.ray', 
        compute='_compute_x_ray_reports', 
        string='X-Ray Reports'
    )
    # Pharmacy History
    pharmacy_history_ids = fields.One2many(
        'pharmacy.description', 
        compute='_compute_pharmacy_history', 
        string='Pharmacy History'
    )

    @api.depends('patient_id')
    def _compute_consultation_history(self):
        for record in self:
            record.consultation_history_ids = self.env['patient.registration'].search([
                ('user_id', '=', record.patient_id.id)
            ])

    @api.depends('patient_id')
    def _compute_lab_reports(self):
        for record in self:
            record.lab_report_ids = self.env['doctor.lab.report'].search([
                ('user_ide', '=', record.patient_id.id)
            ])

    @api.depends('patient_id')
    def _compute_mri_reports(self):
        for record in self:
            record.mri_report_ids = self.env['scanning.mri'].search([
                ('user_ide', '=', record.patient_id.id)
            ])

    @api.depends('patient_id')
    def _compute_ct_reports(self):
        for record in self:
            record.ct_report_ids = self.env['scanning.ct'].search([
                ('user_ide', '=', record.patient_id.id)
            ])

    @api.depends('patient_id')
    def _compute_x_ray_reports(self):
        for record in self:
            record.x_ray_report_ids = self.env['scanning.x.ray'].search([
                ('user_ide', '=', record.patient_id.id)
            ])

    @api.depends('patient_id')
    def _compute_pharmacy_history(self):
        for record in self:
            record.pharmacy_history_ids = self.env['pharmacy.description'].search([
                ('patient_id', '=', record.patient_id.id)
            ])


class OpCategory(models.Model):
    _name = 'block'
    _rec_name = 'block'



    block = fields.Char(string='block')