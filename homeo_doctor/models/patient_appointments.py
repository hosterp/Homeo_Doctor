from odoo import api, fields, models, _
import datetime


class PatientAppointment(models.Model):
    _name = 'patient.appointment'
    _description = 'Patient Appointment'
    _rec_name = 'appointment_reference'
    _order = 'appointment_date desc'

    appointment_reference = fields.Char(string="Appointment No", readonly=True)
    patient_id = fields.Many2one('patient.reg', string='Patient', required=True)
    appointment_date = fields.Datetime(string="Appointment Date", required=True)
    doctor_id = fields.Many2one('doctor.profile', string='Doctor', required=True)
    department=fields.Many2one('doctor.department',string='Department',required=True)
    reason = fields.Text(string="Reason for Appointment")
    status = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='draft', string="Status")
    notes = fields.Text(string="Appointment Notes")
    created_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    consultation_fee = fields.Integer(string='Consultation Fee', compute='_compute_consultation_fee', store=True)

    @api.depends('doctor_id', 'patient_id')
    def _compute_consultation_fee(self):
        for record in self:
            if record.patient_id and record.doctor_id and record.appointment_date:
                # Fetch consultation fee details
                consultation_fee_limit = record.doctor_id.consultation_fee_limit or 0
                consultation_fee = record.doctor_id.consultation_fee_doctor or 0

                # Convert appointment_date to date for comparison
                appointment_date = record.appointment_date.date()

                # 1. Check last appointment
                last_appointment = self.env['patient.appointment'].search([
                    ('patient_id', '=', record.patient_id.id),
                    ('doctor_id', '=', record.doctor_id.id),
                    ('id', '!=', record.id) if record.id else ('id', '!=', False),
                ], order='appointment_date desc', limit=1)

                if last_appointment:
                    # Convert last appointment datetime to date
                    last_appointment_date = last_appointment.appointment_date.date()
                    last_appointment_day = (appointment_date - last_appointment_date).days
                    # print("last appointment", last_appointment_day)
                else:
                    last_appointment_day = 0
                    # print("appointment set zero")

                # 2. Check last registration
                last_registration = self.env['patient.reg'].search([
                    ('patient_id', '=', record.patient_id.patient_id),
                    ('doc_name', '=', record.doctor_id.id),
                ], order='formatted_date desc', limit=1)

                # print('last register read', last_registration.read())
                # print("register object date ", last_registration.date)

                if last_registration:
                    # last_registration.date is already a date object, no need to convert
                    last_registration_day = (appointment_date - last_registration.date).days
                    # print("last register", last_registration_day)
                else:
                    last_registration_day = 0
                    # print("register set zero")

                # Compare the two days and choose the larger value for delta_days
                if last_registration_day != 0 and last_appointment_day != 0:
                    delta_days = min(last_registration_day, last_appointment_day)
                elif last_appointment_day != 0 and last_registration_day == 0:
                    delta_days = last_appointment_day
                elif last_appointment_day == 0 and last_registration_day != 0:
                    delta_days = last_registration_day
                else:
                    record.consultation_fee = consultation_fee
                    return

                if last_registration_day or last_appointment_day != 0:
                    # Apply the consultation fee logic
                    if last_appointment or last_registration:
                        if delta_days <= consultation_fee_limit:
                            record.consultation_fee = 0.0
                        else:
                            record.consultation_fee = consultation_fee
                    else:
                        record.consultation_fee = consultation_fee
                else:
                    record.consultation_fee = consultation_fee

    @api.model
    def create(self, vals):
        # Automatically compute the consultation fee before saving
        if 'doctor_id' in vals and 'patient_id' in vals and 'appointment_date' in vals:
            doctor = self.env['doctor.profile'].browse(vals['doctor_id'])
            consultation_fee_limit = doctor.consultation_fee_limit or 0
            consultation_fee = doctor.consultation_fee_doctor or 0

            # Search for the last appointment for the same patient and doctor
            last_appointment = self.search(
                [
                    ('patient_id', '=', vals['patient_id']),
                    ('doctor_id', '=', vals['doctor_id']),
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
                    'doctor_id': [('department_id', '=', self.department.id)],
                }
            }
        return {
            'domain': {
                'doctor_id': []
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



