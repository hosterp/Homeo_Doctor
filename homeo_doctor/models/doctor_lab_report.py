from email.policy import default

from odoo import api, fields, models, _


# from odoo.odoo.exceptions import UserError


class DoctorLabReport(models.Model):
    _name = 'doctor.lab.report'
    _description = 'Doctor Lab Report'
    _rec_name = 'report_reference'
    _order = 'date desc'

    user_ide = fields.Many2one('patient.reg', string="UHID")
    patient_id = fields.Many2one('patient.registration', string="Consultation ID")
    patient_name = fields.Char(string="Patient Name")
    patient_phone = fields.Char(related='patient_id.phone_number', string="Patient Mobile Number")
    reference_no = fields.Char(string="Reference No")
    report_reference = fields.Char(string="Report Reference", readonly=True, default=lambda self: _('New'))
    date = fields.Date(string="Report Date", default=fields.Date.context_today)
    doctor_id = fields.Many2one('doctor.profile', string="Doctor")
    report_details = fields.Text(string="Report Details")
    attachment = fields.Binary(string="Result")
    attachment_name = fields.Char(string="Result")
    bill_amount = fields.Integer('Bill Amount')
    referral_id = fields.Many2one('lab.referral', string="Referral ID")
    referral_details = fields.Text(string="Referral Details")
    lab_reference_no = fields.Many2one('lab.referral', 'Reference No')
    lab_line_ids = fields.One2many('lab.scan.line', 'lab_id', string='Lab Lines')
    vssc_check = fields.Boolean(string="VSSC")

    # with register
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
    consultation_check = fields.Boolean(default=True)
    alternate_phone = fields.Char("Alternate Mobile Number")

    @api.onchange('user_ide')
    def _onchange_user_ide(self):
        """
        Automatically populate patient details when UHID is selected
        and manage field visibility
        """
        if self.user_ide:
            # Search for patient registration record
            patient_reg = self.env['patient.reg'].browse(self.user_ide.id)

            if patient_reg:
                # Switch to non-registered patient view
                self.register_visible = False

                # Populate patient name for non-registered view
                self.patient_name = patient_reg.patient_id

                # Optionally, populate other details
                self.patient_phone = patient_reg.phone_number
                self.vssc_check = patient_reg.vssc_boolean

                # Optionally, if you want to link to patient registration
                # patient_registration = self.env['patient.registration'].search([
                #     ('name', '=', patient_reg.patient_id),
                #     ('phone_number', '=', patient_reg.phone_number)
                # ], limit=1)

                # if patient_registration:
                #     self.patient_id = patient_registration.id
            else:
                # Reset fields if no patient found
                self.register_visible = True
                self.patient_name = False
                self.patient_phone = False
                self.patient_id = False

    def action_walk_in_patient(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Walk-in Patients',
            'res_model': 'doctor.lab.report',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('homeo_doctor.view_lab_walk_in_tree').id, 'tree'),
                      (self.env.ref('homeo_doctor.view_lab_report_form').id, 'form')],
            'domain': [('register_visible', '=', True)],
            'target': 'current',
        }

    def action_confirm_payment(self):
        """ Open the Lab Payment wizard and pre-fill data from multiple selected records """
        if len(self) > 1:
            raise ValueError("Please select only one record at a time.")

        total_amount = sum(self.lab_line_ids.mapped('total_amount'))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Payment',
            'res_model': 'lab.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.user_ide.id if self.user_ide else False,
                'default_patient_name': self.patient_name,
                'default_total_amount': total_amount,
            }
        }

    # @api.model
    # def create(self, vals):
    #     record = super(DoctorLabReport, self).create(vals)
    #     self.env['patient.reg'].create({
    #         'patient_id': record.register_patient_name,
    #         'address': record.register_address,
    #         'age': record.register_age,
    #         'email': record.register_email,
    #         'phone_number': record.register_phone_number,
    #         'registration_fee': record.registration_fee,
    #
    #     })
    #     return record

    @api.model
    def create(self, vals):
        # Generate report reference if not provided
        if vals.get('report_reference', _('New')) == _('New'):
            vals['report_reference'] = self.env['ir.sequence'].next_by_code('doctor.lab.report') or _('New')

        # Check if registration is visible and patient name is provided
        if vals.get('register_visible', True) and vals.get('register_patient_name'):
            # Prepare patient registration values
            patient_reg_vals = {
                'patient_id': vals.get('register_patient_name'),
                'address': vals.get('register_address'),
                'age': vals.get('register_age'),
                'email': vals.get('register_email'),
                'phone_number': vals.get('register_phone_number'),
                'registration_fee': vals.get('registration_fee', 50.0),
                'consultation_check': vals.get('consultation_check', True),
                'walk_in': True

            }
            print(patient_reg_vals)

            # Create patient registration
            self.env['patient.reg'].create(patient_reg_vals)

        # Create the lab report
        return super(DoctorLabReport, self).create(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(DoctorLabReport, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        if self.env.user.has_group('base.group_user'):
            doc_id = self.env['doctor.profile'].search([('user_id', '=', self.doctor_id.user_id.id)], limit=1)
            if doc_id:
                domain = [('doctor_id', '=', doc_id.id)]
                res['arch'] = res['arch'].replace('<tree', f'<tree domain="{domain}"')
        return res

    def action_add_report(self, report_details):

        for scan in self:
            report = self.env['doctor.lab.report'].create({
                'referral_id': scan.referral_id.id,
                'patient_id': scan.patient_id.id,
                'report_details': report_details,
            })

            scan.referral_id.write({
                'lab_report_id': report.id
            })

        return True

    # @api.onchange('user_ide')
    # def _onchange_patient_id(self):
    #     if self.user_ide:
    #         latest_referral = self.env['lab.referral'].search(
    #             [('user_ide', '=', self.user_ide.id)],
    #             order='create_date desc',
    #             limit=1
    #         )
    #         self.lab_reference_no = latest_referral.id if latest_referral else False
    #         self.referral_details=latest_referral.details if latest_referral else False
    #         self.patient_id = latest_referral.patient_id if latest_referral else False

    def print_invoice(self):
        return self.env.ref('homeo_doctor.action_report_lab_invoice').report_action(self)


class LabType(models.Model):
    _name = 'lab.type'
    _description = 'Type of Lab Test'

    name = fields.Char(string='Test Description', required=True)


class LabRate(models.Model):
    _name = 'lab.rate'
    _description = 'Lab Test Rate'
    _rec_name = 'amount'  # This will display the amount in Many2one fields

    amount = fields.Float(string='Amount', required=True)


class LabScanLine(models.Model):
    _name = 'lab.scan.line'
    _description = 'Lab Scan Line'

    lab_id = fields.Many2one('doctor.lab.report', string='Lab Test')
    lab_type_id = fields.Many2one(
        'lab.investigation',
        string='Investigation',
    )

    lab_department = fields.Many2one(
        'lab.department',
        string='Department',
    )
    rate_id = fields.Monetary(
        string='Rate',
        compute='_compute_rate',
        store=True,
    readonly = False
    )
    total_amount = fields.Monetary(
        string="Total",
        compute='_compute_total_amount',
        store=True
    )
    lab_result = fields.Char('Result')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # @api.onchange('lab_department')
    # def _onchange_lab_department(self):
    #     """Filter Investigations based on selected Lab Department"""
    #     if self.lab_department:
    #         return {
    #             'domain': {'lab_type_id': [('lab_department', '=', self.lab_department.id)]}
    #         }
    #     else:
    #         return {
    #             'domain': {'lab_type_id': []}  # No filter when department is not selected
    #         }

    @api.depends('lab_type_id')
    def _compute_rate(self):
        for record in self:
            if record.lab_type_id:
                record.rate_id = record.lab_type_id.rate
            else:
                record.rate_id = 0.0

    @api.depends('rate_id')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.rate_id
