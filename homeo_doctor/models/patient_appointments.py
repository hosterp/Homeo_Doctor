from odoo import api, fields, models, _
import datetime

from dateutil.relativedelta import relativedelta

from odoo.addons.test_convert.tests.test_env import record


class PatientAppointment(models.Model):
    _name = 'patient.appointment'
    _description = 'Patient Appointment'
    _rec_name = 'appointment_reference'
    _order = 'appointment_date desc'

    appointment_reference = fields.Char(string="Appointment No", readonly=True)
    token_no = fields.Char("Token No")
    patient_id = fields.Many2one('patient.reg', string='UHID', required=True)
    patient_name= fields.Char(related='patient_id.patient_id', string='Patient Name', required=True)
    appointment_date = fields.Date(string="Appointment Date")
    doctor_id = fields.Many2one('doctor.profile', string='Doctor')
    department=fields.Many2one('doctor.department',string='Department')
    departments=fields.Many2many('doctor.department',string='Departments')
    reason = fields.Text(string="Reason for Appointment")
    status = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='draft', string="Status")
    notes = fields.Text(string="Appointment Notes")
    created_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    consultation_fee = fields.Integer(string='Consultation Fee',compute='_compute_consultation_fee')
    address = fields.Text(related='patient_id.address',string='Address')
    age = fields.Integer(related='patient_id.age',string='Age')
    phone_number = fields.Char(related='patient_id.phone_number',string='Phone Number')
    gender = fields.Selection(related='patient_id.gender',string='Gender')
    button_visible = fields.Boolean(default=True)
    doctor_ids = fields.Many2many('doctor.profile', string='Doctors')
    consultation_fee_ids = fields.One2many('appointment.fee', 'appointment_id', string='Consultation Fees')
    registration_fee = fields.Integer(
        string="Registration Fee",
        store=True
    )
    status = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='draft', string="Status")
    payment_method = fields.Selection([
    ('cash', 'Cash'),
    ('upi', 'UPI'),
    ('card', 'Card')
    ], string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')

    register_total_amount = fields.Integer(string="Total Amount", compute="_compute_register_total")
    register_amount_paid = fields.Integer(string="Amount Paid")
    register_balance = fields.Integer(string="Balance")
    register_staff_name = fields.Char("Staff Name")
    register_staff_password = fields.Char("Password")
    register_mode_payment = fields.Selection([('cash', 'Cash'),
                                              ('card', 'Card'),
                                              ('cheque', 'Cheque'),
                                              ('credit','Credit'),
                                              ('upi', 'Mobile Pay'), ], string='Payment Method', default='cash')
    register_card_no = fields.Char(string="Card No")
    register_bank_name = fields.Char(string="Bank")

    def cancel_appointment(self):

        for appointment in self:

            # Update this appointment's status

            appointment.write({

                'status': 'cancelled',

                'button_visible': False

            })

            # Find all patient.registration records created from this appointment

            # by matching patient_id and appointment_date

            related_registrations = self.env['patient.registration'].search([

                ('patient_id', '=', appointment.patient_id.id),

                ('appointment_date', '=', appointment.appointment_date),

                ('doctor', 'in', appointment.doctor_ids.ids),

                ('status', 'in', ['confirmed', 'completed'])

            ])

            if related_registrations:
                related_registrations.write({'status': 'cancelled'})

        return True

    @api.depends('registration_fee', 'consultation_fee')
    def _compute_register_total(self):
        for rec in self:
            reg_fee = rec.registration_fee if rec.registration_fee else 0
            rec.register_total_amount = reg_fee + (rec.consultation_fee or 0)

    appointment_id = fields.Many2one('patient.appointment', string='Appointment', readonly=True)


    def action_confirm_payment(self):
        for appointment in self:
            # Update appointment with payment information
            appointment.write({
                'payment_method': appointment.payment_method,
                'payment_reference': appointment.payment_reference,
                'status': 'confirmed',
                'button_visible': False
            })

            # Check if patient.registration model has payment_method and payment_reference
            registration_model = self.env['patient.registration']
            has_payment_fields = all(field in registration_model._fields
                                     for field in ['payment_method', 'payment_reference'])

            # Parse token numbers
            token_numbers = [token.strip() for token in (appointment.token_no or '').split(',') if token.strip()]

            # Create registrations for each doctor
            for index, doctor in enumerate(appointment.doctor_ids):
                token_no = token_numbers[min(index, len(token_numbers) - 1)] if token_numbers else appointment.token_no

                registration_vals = {
                    'user_id': appointment.patient_id.id,
                    'patient_id': appointment.patient_id.id,
                    'token_no': token_no,
                    'address': appointment.patient_id.address,
                    'age': appointment.patient_id.age,
                    'phone_number': appointment.patient_id.phone_number,
                    'doctor': doctor.id,
                    'appointment_date': appointment.appointment_date,
                    'status': 'confirmed',
                }

                if has_payment_fields:
                    registration_vals.update({
                        'payment_method': appointment.payment_method,
                        'payment_reference': appointment.payment_reference,
                    })

                registration_model.create(registration_vals)
        return self.env.ref('homeo_doctor.action_report_patient_appointment').report_action(appointment)

        # return {'type': 'ir.actions.act_window_close'}

    @api.onchange('appointment_date')
    def _compute_registration_fee(self):
        for record in self:
            if record.patient_id:
                # Get the patient's last track registration date
                last_track_date = record.patient_id.track_registration_date
                # print("last register day")

                # Calculate the difference between appointment date and last track registration date
                if last_track_date:
                    date_difference = relativedelta(record.appointment_date, last_track_date)
                    # print("difference", date_difference)

                    # Check if the difference is less than 1 year
                    if date_difference.years < 1:
                        record.registration_fee = 0
                        # print("register is 0")
                    else:
                        # Get the registration fee from patient.registration.fee model
                        registration_fee_record = self.env['patient.registration.fee'].search([], limit=1)
                        record.registration_fee = registration_fee_record.fee if registration_fee_record else 0
                        # print("register fee", record.registration_fee )

                        # Update track registration date
                        record.patient_id.track_registration_date = record.appointment_date
                else:
                    # If no previous track registration date, get the fee from patient.registration.fee
                    registration_fee_record = self.env['patient.registration.fee'].search([], limit=1)
                    record.registration_fee = registration_fee_record.fee if registration_fee_record else 0
                    # print("If no previous track registration date")

                    # Set track registration date
                    record.patient_id.track_registration_date = record.appointment_date
            else:
                record.registration_fee = 0
                # print("no id")



    def action_cancel(self):
        for record in self:
            record.status = 'cancelled'

    @api.onchange('departments')
    def _onchange_departments(self):
        if self.departments:
            department_ids = self.departments.ids

            doctors = self.env['doctor.profile'].search([('department_id', 'in', department_ids)])

            return {
                'domain': {'doctor_ids': [('id', 'in', doctors.ids)]}
            }
        else:

            return {
                'domain': {'doctor_ids': []}
            }

    @api.depends('doctor_ids')
    def _compute_consultation_fee(self):
        for record in self:
            record.consultation_fee = 0
            # print(f"Initial consultation_fee set to: {record.consultation_fee}")

            for doctor in record.doctor_ids:
                if record.patient_id and doctor and record.appointment_date:

                    # Fetch consultation fee details
                    consultation_fee_limit = doctor.consultation_fee_limit or 0
                    consultation_fee = doctor.consultation_fee_doctor or 0
                    print(f"consultation_fee_limit: {consultation_fee_limit}, consultation_fee: {consultation_fee}")

                    # Convert appointment_date to date for comparison
                    appointment_date = record.appointment_date
                    print(f"Converted appointment_date to: {appointment_date}")

                    # 1. Check last appointment
                    last_appointment = self.env['patient.appointment'].search([
                        ('patient_id', '=', record.patient_id.id),
                        ('doctor_ids', '=', doctor.id),
                        ('id', '!=', record.id) if record.id else ('id', '!=', False),
                    ], order='appointment_date desc', limit=1)

                    if last_appointment:
                        last_appointment_date = last_appointment.appointment_date
                        last_appointment_day = (appointment_date - last_appointment_date).days
                        print(
                            f"Last appointment found. Last appointment date: {last_appointment_date}, days since last appointment: {last_appointment_day}")
                    else:
                        last_appointment_day = 0
                        print("No previous appointment found. Set last_appointment_day to 0.")

                    # 2. Check last registration
                    last_registration = self.env['patient.reg'].search([
                        ('patient_id', '=', record.patient_id.patient_id),
                        ('doc_name', '=', doctor.id),
                    ], order='formatted_date desc', limit=1)

                    if last_registration:
                        last_registration_day = (appointment_date - last_registration.date).days
                        print(
                            f"Last registration found. Last registration date: {last_registration.date}, days since last registration: {last_registration_day}")
                    else:
                        last_registration_day = 0
                        print("No previous registration found. Set last_registration_day to 0.")

                    # Compare the two days and choose the larger value for delta_days
                    if last_registration_day != 0 and last_appointment_day != 0:
                        delta_days = min(last_registration_day, last_appointment_day)
                        print(f"Both last registration and last appointment exist. delta_days set to: {delta_days}")
                    elif last_appointment_day != 0 and last_registration_day == 0:
                        delta_days = last_appointment_day
                        print(f"Only last appointment exists. delta_days set to: {delta_days}")
                    elif last_appointment_day == 0 and last_registration_day != 0:
                        delta_days = last_registration_day
                        print(f"Only last registration exists. delta_days set to: {delta_days}")
                    else:
                        record.consultation_fee += consultation_fee
                        print(f"No previous registration or appointment. Adding consultation fee: {consultation_fee}")
                        continue

                    if last_registration_day or last_appointment_day != 0:
                        # Apply the consultation fee logic
                        if delta_days <= consultation_fee_limit:
                            print(f"delta_days <= consultation_fee_limit. No additional fee added.")
                            record.consultation_fee += 0.0
                        else:
                            print(f"delta_days > consultation_fee_limit. Adding consultation fee: {consultation_fee}")
                            record.consultation_fee += consultation_fee
                    else:
                        record.consultation_fee += consultation_fee
                        print(f"No last registration or appointment. Adding consultation fee: {consultation_fee}")

    # @api.depends('doctor_ids', 'appointment_date', 'patient_id')
    # def _compute_consultation_fee(self):
    #     for record in self:
    #
    #         record.consultation_fee = 0.0
    #
    #
    #         if record.patient_id and record.appointment_date:
    #             appointment_date = record.appointment_date.date()
    #
    #
    #             if record.doctor_id:
    #             #     doctors_to_process = [record.doctor_id]
    #             # else:
    #                 doctors_to_process = record.doctor_ids
    #
    #             total_fee = 0.0
    #
    #
    #             print(f"Doctors to process: {doctors_to_process}")
    #
    #
    #             for doctor in doctors_to_process:
    #                 print(f"Processing doctor: {doctor.name}")
    #
    #
    #                 consultation_fee_limit = doctor.consultation_fee_limit or 0
    #                 consultation_fee = doctor.consultation_fee_doctor or 0
    #
    #
    #                 last_appointment = self.env['patient.appointment'].search([
    #                     ('patient_id', '=', record.patient_id.id),
    #                     ('doctor_id', '=', doctor.id),
    #                     ('id', '!=', record.id) if record.id else ('id', '!=', False),
    #                 ], order='appointment_date desc', limit=1)
    #
    #                 last_appointment_day = (
    #                     (appointment_date - last_appointment.appointment_date.date()).days
    #                     if last_appointment else float('inf')
    #                 )
    #
    #
    #                 last_registration = self.env['patient.reg'].search([
    #                     ('patient_id', '=', record.patient_id.patient_id),
    #                     ('doc_name', '=', doctor.id),
    #                 ], order='formatted_date desc', limit=1)
    #
    #                 last_registration_day = (
    #                     (appointment_date - last_registration.date).days
    #                     if last_registration else float('inf')
    #                 )
    #
    #
    #                 delta_days = min(last_appointment_day, last_registration_day)
    #
    #
    #                 fee = 0.0 if delta_days <= consultation_fee_limit else consultation_fee
    #
    #
    #                 total_fee += fee
    #
    #
    #                 self.env['appointment.fee'].create({
    #                     'appointment_id': record.id,
    #                     'doctor_id': doctor.id,
    #                     'consultation_fee': fee,
    #                 })
    #
    #
    #             print(f"Total consultation fee for this appointment: {total_fee}")
    #
    #
    #             record.consultation_fee = total_fee
    #             print( record.consultation_fee,' record.consultation_fee...............................')

    def action_appointment_confirm(self):
        self.ensure_one()

        # Only set status and button_visible, don't create registrations yet
        self.status = 'confirmed'
        self.button_visible = False

        # Create wizard
        wizard_vals = {
            'patient_id': self.patient_id.id,
            'patient_name': self.patient_name,
            'appointment_id': self.id,
            'total_fee': self.consultation_fee,
            'doctor_ids': [(6, 0, self.doctor_ids.ids)],
        }

        wizard = self.env['appointment.payment.wizard'].create(wizard_vals)

        # Create fee lines
        for doctor in self.doctor_ids:
            # Get consultation fee for this doctor
            doc_fee = 0
            for fee in self.consultation_fee_ids:
                if fee.doctor_id.id == doctor.id:
                    doc_fee = fee.consultation_fee
                    break

            # If no fee found in consultation_fee_ids, calculate it
            if doc_fee == 0 and hasattr(doctor, 'consultation_fee_doctor'):
                doc_fee = doctor.consultation_fee_doctor

            # Create fee line
            self.env['wizard.appointment.fee'].create({
                'wizard_id': wizard.id,
                'doctor_id': doctor.id,
                'fee_amount': doc_fee
            })

        return {
            'name': 'Appointment Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'appointment.payment.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }
            # return {
            #     'type': 'ir.actions.act_window',
            #     'name': 'Patient Registration',
            #     'res_model': 'patient.registration',
            #     'view_mode': 'form',
            #     'res_id': patient_registration.id,
            #     'target': 'new',
            # }
    @api.model
    def create(self, vals):
        # Automatically compute the consultation fee before saving
        if 'doctor_ids' in vals and 'patient_id' in vals and 'appointment_date' in vals:
            doctor = self.env['doctor.profile'].browse(vals['doctor_id'])
            consultation_fee_limit = doctor.consultation_fee_limit or 0
            consultation_fee = doctor.consultation_fee_doctor or 0

            # Search for the last appointment for the same patient and doctor
            last_appointment = self.search(
                [
                    ('patient_id', '=', vals['patient_id']),
                    ('doctor_ids', '=', vals['doctor_id']),
                ],
                order='appointment_date desc',
                limit=1
            )

            if last_appointment:
                # Calculate the difference in days
                delta_days = (
                        fields.Date.from_string(vals['appointment_date']) - last_appointment.appointment_date).days
                if delta_days <= consultation_fee_limit:
                    vals['consultation_fee'] = 0.0
                else:
                    vals['consultation_fee'] = consultation_fee
            else:
                # No previous appointment found; apply the default consultation fee
                vals['consultation_fee'] = consultation_fee

        return super(PatientAppointment, self).create(vals)

    @api.onchange('department')
    def _onchange_department_id(self):
        if self.department:
            return {
                'domain': {
                    'doctor_ids': [('department_id', '=', self.department.id)],
                }
            }
        return {
            'domain': {
                'doctor_ids': []
            }
        }

    @api.model
    def create(self, vals):
        if vals.get('appointment_reference', 'New') == 'New':
            appointment_ref = self.env['ir.sequence'].next_by_code('patient.appointment.sequence')
            vals['appointment_reference'] = appointment_ref or 'New'

        # For multiple doctors, generate token for each doctor
        if vals.get('doctor_ids') and isinstance(vals['doctor_ids'], list):
            token_numbers = []
            appointment_date = fields.Date.from_string(vals.get('appointment_date')) if vals.get(
                'appointment_date') else None

            for cmd in vals['doctor_ids']:
                if cmd[0] == 6 and cmd[2]:  # Command 6 is set
                    doctor_ids = cmd[2]
                    for doctor_id in doctor_ids:
                        doctor = self.env['doctor.profile'].browse(doctor_id)
                        if doctor:
                            token_number = doctor.get_next_token_number(appointment_date)
                            if token_number:
                                token_numbers.append(token_number)

            if token_numbers:
                vals['token_no'] = ", ".join(token_numbers)

        return super(PatientAppointment, self).create(vals)


    @api.model
    def search_appointments_by_patient(self, patient_id):

        return self.search([('patient_id', '=', patient_id)])



class AppointmentFee(models.Model):
    _name = 'appointment.fee'
    _description = 'Consultation Fee Per Doctor'

    appointment_id = fields.Many2one('patient.appointment', string='Appointment')
    doctor_id = fields.Many2one('doctor.profile', string='Doctor')
    consultation_fee = fields.Float(string='Consultation Fee')
