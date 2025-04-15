from odoo import api, fields, models, _

class AdmittedPatient(models.Model):
    _name = 'hospital.admitted.patient'
    _description = 'Admitted Patient Details'
    _rec_name = 'patient_id'
    _order = 'admission_date desc'

    patient_id = fields.Many2one('patient.reg', string="Patient", required=True)
    name = fields.Char(related='patient_id.patient_id', string="Patient Name", required=True)
    age = fields.Integer(related='patient_id.age', string="Age", readonly=True)
    gender = fields.Selection(related='patient_id.gender', string="Gender", readonly=True)
    phone_number = fields.Char(related='patient_id.phone_number', string="Phone Number", readonly=True)
    email = fields.Char(related='patient_id.email', string="Email", readonly=True)
    address = fields.Text(related='patient_id.address', string="Address", readonly=True)
    medical_records=fields.Many2one('hospital.ot')
    dob=fields.Date(related='patient_id.dob',string='Date of Birth')

    emergency_contact_name = fields.Char(string="Emergency Contact Name")
    emergency_contact_phone = fields.Char(string="Emergency Contact Phone")
    emergency_contact_relation = fields.Char(string="Relationship to Patient")


    admission_date = fields.Datetime(string="Admission Date", required=True, default=fields.Datetime.now)
    room_number = fields.Char(string="Room Number")
    bed_number = fields.Char(string="Bed Number")
    admitting_department = fields.Selection([
        ('general', 'General'),
        ('surgery', 'Surgery'),
        ('icu', 'ICU'),
        ('emergency', 'Emergency'),
    ], string="Admitting Department",)
    attending_doctor = fields.Many2one('doctor.profile', string="Attending Doctor", required=True)
    reason_for_admission = fields.Text(string="Reason for Admission")
    admission_status = fields.Selection([
        ('regular', 'Regular'),
        ('emergency', 'Emergency'),
        ('icu', 'ICU'),
    ], string="Admission Status")



    current_diagnosis = fields.Text(string="Current Diagnosis")
    medications_prescribed = fields.Text(string="Medications Prescribed")
    allergies = fields.Text(string="Allergies")
    test_results = fields.Text(string="Test Results")


    procedures_scheduled = fields.Text(string="Scheduled Procedures")
    treatment_description = fields.Text(string="Treatment Description")
    daily_progress_notes = fields.Text(string="Daily Progress Notes")
    consultation_notes = fields.Text(string="Consultation Notes")


    insurance_provider = fields.Char(string="Insurance Provider")
    insurance_policy_number = fields.Char(string="Policy Number")
    advance_payment = fields.Float(string="Advance Payment")
    billing_summary = fields.Text(string="Billing Summary")


    discharge_date = fields.Datetime(string="Discharge Date")
    final_diagnosis = fields.Text(string="Final Diagnosis")
    discharge_prescriptions = fields.Text(string="Discharge Prescriptions")
    follow_up_instructions = fields.Text(string="Follow-Up Instructions")
    summary_report = fields.Text(string="Summary Report")
    room_category = fields.Many2one('room.category', string='Room Category')
    advance_amount = fields.Integer(string='Advance Amount')
    status=fields.Selection([('admitted','Admitted'),('discharged','Discharged')],default='admitted')
    consultation_id = fields.Many2one('patient.registration', string="Consultation Reference")

    previous_conditions = fields.Text(string="Previous Conditions", compute='_compute_previous_conditions')
    # Field to store previous consultations
    previous_consultation_ids = fields.One2many(
        'patient.registration', 'patient_id',
        string='Previous Consultations',
        compute='_compute_previous_consultations',
        store=False  # You can make it stored if you want to cache the results
    )

    @api.depends('patient_id')
    def _compute_previous_consultations(self):
        for record in self:
            # Only proceed if the record has been saved (i.e., has an id)
            if record.id:
                previous_consultations = self.env['patient.registration'].search([
                    ('patient_id', '=', record.patient_id.id),
                    ('id', '!=', record.id)  # Ensure the current record is excluded
                ])
                record.previous_consultation_ids = previous_consultations
            else:
                # For unsaved records, set to False or an empty record set
                record.previous_consultation_ids = False

    def get_previous_medical_history(self):
        history = ''
        for consultation in self.previous_consultation_ids:
            if consultation.present_medications:
                history += f"Medications: {consultation.present_medications}\n"
            if consultation.allergies:
                history += f"Allergies: {consultation.allergies}\n"
            if consultation.previous_conditions:
                history += f"Previous Conditions: {consultation.previous_conditions}\n"

        return history if history else "No previous medical history available."

    @api.onchange('room_category')
    def onchange_advance_amount(self):
        for i in self:
            if i.room_category:
                i.advance_amount = i.room_category.advance_amount
                i.advance_payment=  i.advance_amount
            else:
                pass
    def action_print_patient_report(self):
        # This will trigger the report action
        return self.env.ref('homeo_doctor.action_admitted_patient_report').report_action(self)