from odoo import api, fields, models, _
import datetime

from odoo.addons.test_convert.tests.test_env import record


class PatientAppointment(models.Model):
    _name = 'patient.appointment'
    _description = 'Patient Appointment'
    _rec_name = 'appointment_reference'
    _order = 'appointment_date desc'

    appointment_reference = fields.Char(string="Appointment No", readonly=True)
    patient_id = fields.Many2one('patient.reg', string='Patient ID', required=True)
    patient_name= fields.Char(related='patient_id.patient_id', string='Patient Name', required=True)
    appointment_date = fields.Datetime(string="Appointment Date")
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
    status = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='draft', string="Status")

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
            print(f"Initial consultation_fee set to: {record.consultation_fee}")

            for doctor in record.doctor_ids:
                if record.patient_id and doctor and record.appointment_date:

                    # Fetch consultation fee details
                    consultation_fee_limit = doctor.consultation_fee_limit or 0
                    consultation_fee = doctor.consultation_fee_doctor or 0
                    print(f"consultation_fee_limit: {consultation_fee_limit}, consultation_fee: {consultation_fee}")

                    # Convert appointment_date to date for comparison
                    appointment_date = record.appointment_date.date()
                    print(f"Converted appointment_date to: {appointment_date}")

                    # 1. Check last appointment
                    last_appointment = self.env['patient.appointment'].search([
                        ('patient_id', '=', record.patient_id.id),
                        ('doctor_ids', '=', doctor.id),
                        ('id', '!=', record.id) if record.id else ('id', '!=', False),
                    ], order='appointment_date desc', limit=1)

                    if last_appointment:
                        last_appointment_date = last_appointment.appointment_date.date()
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
        for record in self:
            # Create separate registration for each doctor
            record.status='confirmed'
            for doctor in record.doctor_ids:
                registration_vals = {
                    'user_id': record.patient_id.reference_no,
                    'patient_id': record.patient_id.patient_id,
                    'address': record.patient_id.address,
                    'age': record.patient_id.age,
                    'phone_number': record.patient_id.phone_number,
                    'doctor_id': doctor.display_name,  # Single doctor name
                    'appointment_date':record.appointment_date,
                }
                patient_registration = self.env['patient.registration'].create(registration_vals)
                patient_registration.status='confirmed'
                print(f'Created registration for doctor {doctor.display_name}: {registration_vals}')

            self.button_visible = False
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
