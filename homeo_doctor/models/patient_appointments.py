from odoo import api, fields, models, _
import datetime
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo.addons.test_convert.tests.test_env import record
import logging

class PatientAppointment(models.Model):
    _name = 'patient.appointment'
    _description = 'Patient Appointment'
    _rec_name = 'appointment_reference'
    _order = 'appointment_date desc'

    appointment_reference = fields.Char(string="Appointment No", readonly=True)
    token_no = fields.Char("Token No")
    patient_id = fields.Many2one('patient.reg', string='UHID', required=True)
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
    consultation_fee = fields.Integer(string='Consultation Fee',compute='_compute_consultation_fee',readonly=False,)
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
    register_staff_name = fields.Many2one('hr.employee',"Staff Name")
    register_staff_password = fields.Char("Password")
    register_mode_payment = fields.Selection([('cash', 'Cash'),
                                              ('card', 'Card'),
                                              ('cheque', 'Cheque'),
                                              ('credit','Credit'),
                                              ('upi', 'Mobile Pay'), ], string='Payment Method', default='cash')
    register_card_no = fields.Char(string="Card No")
    register_bank_name = fields.Char(string="Bank")
    vssc_boolean = fields.Boolean(related='patient_id.vssc_boolean',string='VSSC')
    differance_appointment_days = fields.Integer("No of Days")
    spl_boolean = fields.Boolean(string='Spl Case',default=False)
    staff_boolean = fields.Boolean(string='Staff',default=False)

    def amount_to_text_indian(self):
        """Convert amount to words in Indian format (Rupees and Paise)."""
        try:
            from num2words import num2words
            if self.register_total_amount:
                amount_int = int(self.register_total_amount)
                decimal_part = int(round((self.register_total_amount - amount_int) * 100))

                rupees_text = num2words(amount_int, lang='en_IN').title()
                result = f" {rupees_text}"

                if decimal_part:
                    paise_text = num2words(decimal_part, lang='en_IN').title()
                    result += f" and {paise_text} Paise"

                return result + " Only"
        except Exception as e:
            # Optional: log the error for debugging
            _logger = logging.getLogger(__name__)
            _logger.warning("Failed to convert amount to Indian text: %s", e)

            # Fallback
            return self.currency_id.amount_to_text(self.register_total_amount)

        return ""
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

    payment_receipt_number = fields.Char(
        string="Receipt Number",
        readonly=True,
        copy=False,
        default='/',
    )
    def action_confirm_payment(self):
        for appointment in self:
            if not appointment.payment_receipt_number or appointment.payment_receipt_number == '/':
                # Fetch next from sequence 'payment.receipt'
                raw_seq = self.env['ir.sequence'].next_by_code('payment.receipt') or '0'
                # Zero-pad to 4 digits
                padded_seq = str(raw_seq).zfill(4)

                # Compute fiscal year suffix (e.g. if today is June 2025 → "25-26")
                today = datetime.today().date()
                year_start = today.year % 100
                year_end = (today.year + 1) % 100
                fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

                appointment.payment_receipt_number = f"{padded_seq}/{fiscal_suffix}"

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
                # Check if VSSC is enabled for this patient
                is_vssc = record.patient_id.vssc_boolean
                # print(f"VSSC Boolean: {is_vssc}")

                # If VSSC is true, registration fee is always 0
                if is_vssc:
                    record.registration_fee = 0
                    # print("VSSC patient - registration fee set to 0")
                    # Still update track registration date for VSSC patients
                    if not record.patient_id.track_registration_date:
                        record.patient_id.track_registration_date = record.appointment_date
                        # print("VSSC patient - track registration date set")
                    return

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

    # @api.depends('doctor_ids', 'spl_boolean')
    # def _compute_consultation_fee(self):
    #     for record in self:
    #         record.consultation_fee = 0
    #         # print(f"Initial consultation_fee set to: {record.consultation_fee}")
    #         if record.spl_boolean:
    #             record.consultation_fee = 0
    #             continue
    #         for doctor in record.doctor_ids:
    #             if record.patient_id and doctor and record.appointment_date:
    #
    #                 # Check if VSSC is enabled for this patient
    #                 is_vssc = record.patient_id.vssc_boolean
    #                 print(f"VSSC Boolean: {is_vssc}")
    #
    #                 # Fetch consultation fee details
    #                 consultation_fee_limit = doctor.consultation_fee_limit or 0
    #
    #                 # Set consultation fee based on VSSC status
    #                 if is_vssc:
    #                     consultation_fee = 400  # Fixed fee for VSSC patients
    #                     print(f"VSSC patient - consultation_fee set to: {consultation_fee}")
    #                 else:
    #                     consultation_fee = doctor.consultation_fee_doctor or 0
    #                     print(f"Regular patient - consultation_fee: {consultation_fee}")
    #
    #                 print(f"consultation_fee_limit: {consultation_fee_limit}, consultation_fee: {consultation_fee}")
    #
    #                 # Convert appointment_date to date for comparison
    #                 appointment_date = record.appointment_date
    #                 print(f"Converted appointment_date to: {appointment_date}")
    #
    #                 # 1. Check last appointment
    #                 last_appointment = self.env['patient.appointment'].search([
    #                     ('patient_id', '=', record.patient_id.id),
    #                     ('doctor_ids', '=', doctor.id),
    #                     ('id', '!=', record.id) if record.id else ('id', '!=', False),
    #                 ], order='appointment_date desc', limit=1)
    #
    #                 if last_appointment:
    #                     last_appointment_date = last_appointment.appointment_date
    #                     last_appointment_day = (appointment_date - last_appointment_date).days
    #                     print(
    #                         f"Last appointment found. Last appointment date: {last_appointment_date}, days since last appointment: {last_appointment_day}")
    #                 else:
    #                     last_appointment_day = 0
    #                     print("No previous appointment found. Set last_appointment_day to 0.")
    #
    #                 # 2. Check last registration
    #                 last_registration = self.env['patient.reg'].search([
    #                     ('patient_id', '=', record.patient_id.patient_id),
    #                     ('doc_name', '=', doctor.id),
    #                 ], order='formatted_date desc', limit=1)
    #
    #                 if last_registration:
    #                     last_registration_day = (appointment_date - datetime.combine(last_registration.date, datetime.min.time())).days
    #                     print(
    #                         f"Last registration found. Last registration date: {last_registration.date}, days since last registration: {last_registration_day}")
    #                 else:
    #                     last_registration_day = 0
    #                     print("No previous registration found. Set last_registration_day to 0.")
    #
    #                 # Compare the two days and choose the smaller value for delta_days
    #                 if last_registration_day != 0 and last_appointment_day != 0:
    #                     delta_days = min(last_registration_day, last_appointment_day)
    #                     record.differance_appointment_days = delta_days
    #                     print(f"Both last registration and last appointment exist. delta_days set to: {delta_days}")
    #                 elif last_appointment_day != 0 and last_registration_day == 0:
    #                     delta_days = last_appointment_day
    #                     record.differance_appointment_days = delta_days
    #                     print(f"Only last appointment exists. delta_days set to: {delta_days}")
    #                 elif last_appointment_day == 0 and last_registration_day != 0:
    #                     delta_days = last_registration_day
    #                     record.differance_appointment_days = delta_days
    #                     print(f"Only last registration exists. delta_days set to: {delta_days}")
    #                 else:
    #                     # No previous registration or appointment - first time patient
    #                     if is_vssc:
    #                         # For VSSC patients, registration fee is always 0, but doctor fee applies
    #                         record.consultation_fee += consultation_fee
    #                         print(f"VSSC first-time patient. Adding consultation fee: {consultation_fee}")
    #                     else:
    #                         record.consultation_fee += consultation_fee
    #                         print(f"Regular first-time patient. Adding consultation fee: {consultation_fee}")
    #                     continue
    #
    #                 # Apply the consultation fee logic based on delta_days
    #                 if last_registration_day != 0 or last_appointment_day != 0:
    #                     if delta_days <= consultation_fee_limit:
    #                         print(
    #                             f"delta_days ({delta_days}) <= consultation_fee_limit ({consultation_fee_limit}). No additional fee added.")
    #                         if is_vssc:
    #                             # For VSSC patients within limit, registration fee is 0
    #                             record.consultation_fee += 0.0
    #                             print(f"VSSC patient within limit - no fee added")
    #                         else:
    #                             record.consultation_fee += 0.0
    #                             print(f"Regular patient within limit - no fee added")
    #                     else:
    #                         print(
    #                             f"delta_days ({delta_days}) > consultation_fee_limit ({consultation_fee_limit}). Adding consultation fee: {consultation_fee}")
    #                         if is_vssc:
    #                             # For VSSC patients beyond limit, charge the VSSC consultation fee
    #                             record.consultation_fee += consultation_fee
    #                             print(f"VSSC patient beyond limit - adding VSSC consultation fee: {consultation_fee}")
    #                         else:
    #                             record.consultation_fee += consultation_fee
    #                             print(f"Regular patient beyond limit - adding consultation fee: {consultation_fee}")
    #                 else:
    #                     # Fallback case
    #                     if is_vssc:
    #                         record.consultation_fee += consultation_fee
    #                         print(f"VSSC fallback case. Adding consultation fee: {consultation_fee}")
    #                     else:
    #                         record.consultation_fee += consultation_fee
    #                         print(f"Regular fallback case. Adding consultation fee: {consultation_fee}")
    @api.depends('appointment_date', 'doctor_ids', 'patient_id')
    def _compute_consultation_fee(self):
        debug_mode = True  # 🔑 toggle this for debugging

        for record in self:
            record.consultation_fee = 0
            record.differance_appointment_days = 0

            if not record.doctor_ids or not record.patient_id or not record.appointment_date:
                continue

            doctor = record.doctor_ids[0]  # assume single doctor
            consultation_fee = doctor.consultation_fee_doctor or 0
            consultation_fee_limit = doctor.consultation_fee_limit or 7
            is_vssc = record.patient_id.vssc_boolean

            # fetch ALL appointments of this patient with this doctor (ordered oldest → newest)
            all_appts = self.env['patient.appointment'].search([
                ('patient_id', '=', record.patient_id.id),
                ('doctor_ids', '=', doctor.id),
            ], order='appointment_date asc')

            last_fee_date = None
            fee_to_apply = 0

            for appt in all_appts:
                if not last_fee_date:
                    # First appointment → charge consultation fee
                    fee_to_apply = 400 if is_vssc else consultation_fee
                    last_fee_date = appt.appointment_date
                    if debug_mode:
                        pass
                        # print(f"[{appt.appointment_date}] First visit → Fee {fee_to_apply}")
                else:
                    if appt.appointment_date and last_fee_date:
                        # Convert to date if they are datetime objects
                        appt_date = appt.appointment_date.date() if isinstance(appt.appointment_date,
                                                                               datetime) else appt.appointment_date
                        last_date = last_fee_date.date() if isinstance(last_fee_date, datetime) else last_fee_date

                        delta_days = (appt_date - last_date).days
                    else:
                        delta_days = 0
                    if debug_mode:
                        pass
                        # print(f"[{appt.appointment_date}] Days since last fee: {delta_days}")

                    if delta_days <= consultation_fee_limit:
                        fee_to_apply = 0
                        if debug_mode:
                            pass
                            # print(f" → Within {consultation_fee_limit} days → Fee {fee_to_apply}")
                    else:
                        fee_to_apply = 400 if is_vssc else consultation_fee
                        last_fee_date = appt.appointment_date  # 🔑 reset cycle
                        if debug_mode:
                            pass
                            # print(f" → Beyond {consultation_fee_limit} days → Fee {fee_to_apply} (reset cycle)")

                # assign fee ONLY to the current record
                if appt.id == record.id:
                    record.consultation_fee = fee_to_apply
                    record.differance_appointment_days = (
                                appt.appointment_date.date() - last_fee_date.date()).days if last_fee_date else 0
                    if debug_mode:
                        print(f" ✔ Applied to current record {record.id} → Fee {fee_to_apply}")

    @api.onchange('appointment_date', 'spl_boolean', 'staff_boolean')
    def _compute_consultation_fee(self):
        for record in self:
            record.consultation_fee = 0
            record.differance_appointment_days = 0

            if record.spl_boolean:
                record.consultation_fee = 0
                continue
            if record.staff_boolean:
                record.consultation_fee = 150
                continue

            for doctor in record.doctor_ids:
                if not (record.patient_id and doctor and record.appointment_date):
                    continue

                # Check if VSSC is enabled
                is_vssc = record.patient_id.vssc_boolean
                consultation_fee_limit = doctor.consultation_fee_limit or 7
                consultation_fee = 400 if is_vssc else (doctor.consultation_fee_doctor or 0)

                # Fetch all past appointments (including current one in order)
                all_appts = self.env['patient.appointment'].search([
                    ('patient_id', '=', record.patient_id.id),
                    ('doctor_ids', '=', doctor.id),
                ], order='appointment_date asc')

                last_fee_date = None
                fee_to_apply = 0
                delta_days = 0

                for appt in all_appts:
                    if not last_fee_date:
                        # First ever appointment → apply fee
                        fee_to_apply = consultation_fee
                        last_fee_date = appt.appointment_date
                        if appt.id == record.id:
                            record.consultation_fee = fee_to_apply
                            record.differance_appointment_days = 0
                            # print(f"[{appt.appointment_date}] First visit → Fee {fee_to_apply}")
                    else:
                        if appt.appointment_date and last_fee_date:
                            # Convert to date if they are datetime objects
                            appt_date = appt.appointment_date.date() if isinstance(appt.appointment_date,
                                                                                   datetime) else appt.appointment_date
                            last_date = last_fee_date.date() if isinstance(last_fee_date, datetime) else last_fee_date

                            delta_days = (appt_date - last_date).days
                        else:
                            delta_days = 0
                        if delta_days > consultation_fee_limit:
                            # Reset cycle → charge again
                            fee_to_apply = consultation_fee
                            last_fee_date = appt.appointment_date
                            if appt.id == record.id:
                                record.consultation_fee = fee_to_apply
                                record.differance_appointment_days = delta_days
                                # print(
                                #     f"[{appt.appointment_date}] Beyond limit ({consultation_fee_limit}) → Fee {fee_to_apply}, reset baseline")
                        else:
                            # Within limit → no fee
                            fee_to_apply = 0
                            if appt.id == record.id:
                                record.consultation_fee = fee_to_apply
                                record.differance_appointment_days = delta_days
                                # print(
                                #     f"[{appt.appointment_date}] Within limit ({consultation_fee_limit}) → Fee {fee_to_apply}, delta {delta_days}")                            # print(f"Regular fallback case. Adding consultation fee: {consultation_fee}")
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
