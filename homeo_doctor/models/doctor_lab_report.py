from datetime import date
from email.policy import default

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# from odoo.odoo.exceptions import UserError
import logging

class DoctorLabReport(models.Model):
    _name = 'doctor.lab.report'
    _description = 'Doctor Lab Report'
    _rec_name = 'report_reference'
    _order = 'report_reference desc'

    user_ide = fields.Many2one('patient.reg', string="UHID")
    patient_id = fields.Many2one('patient.registration', string="Consultation ID")
    patient_name = fields.Char(string="Patient Name")
    patient_phone = fields.Char(related='patient_id.phone_number', string="Mobile No")
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
    lab_billing_ids = fields.One2many('lab.billing.page', 'lab_billing_id', string='Lab billing Lines')
    vssc_check = fields.Boolean(string="VSSC")
    admitted_check =  fields.Boolean(string="Admitted")
    bill_type = fields.Selection([
        ('op','OP'),('admitted','Admitted Patient'),('others','Others')],string="Bill Type")
    age=fields.Integer('Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    remarks = fields.Text("Remarks")
    staff_name = fields.Many2one('hr.employee',"Staff Name")
    staff_pwd = fields.Char(string='Staff Password')
    o_c_percentage = fields.Char("OC%")
    o_c = fields.Char("OC")
    mode_of_payment = fields.Selection([('cash', 'Cash'),
                                        ('card', 'Card'),
                                        ('upi', 'UPI'),('credit','Credit')], string='Payment Method',default='cash')
    staff_passwor = fields.Char("Staff Password")
    c_o = fields.Boolean("C/O")
    b_o = fields.Boolean("B/O")

    # with register
    register_visible = fields.Boolean(default=False)
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
    alternate_phone = fields.Char("Alternate Mobile No")
    status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('credit','Credit'),
    ], string="Status", default="unpaid", tracking=True)
    sample_status=fields.Selection([
        ('sample_collected', 'Sample Collected'),
        ('pending', 'Pending'),
    ], string="Status", default="pending", tracking=True)
    result_status=fields.Selection([
        ('result_ready', 'Result Ready'),
        ('pending', 'Result Pending'),
    ], string="Status", default="pending", tracking=True)
    grouped_lab_details = fields.Html(compute='_compute_grouped_lab_details', string="Lab Details", sanitize=False)
    total_bill_amount = fields.Integer("Total Amount",compute="_onchange_lab_billing_ids")
    # display_amount = fields.Integer('Bill Amount')
    amount_paid = fields.Integer(string='Amount Paid')
    balance = fields.Integer(string='Balance')
    active_investigation_type = fields.Selection([
        ('all', 'All'),
        ('xray', 'X-Ray'),
        ('mri', 'MRI'),
        ('lab', 'Lab')
    ], string="Active Investigation Type", default='all')
    admitted_patient_id = fields.Many2one('hospital.admitted.patient', string="Admitted Patient")
    def amount_to_text_indian(self):
        """Convert amount to words in Indian format (Rupees and Paise)."""
        try:
            from num2words import num2words
            if self.total_bill_amount:
                amount_int = int(self.total_bill_amount)
                decimal_part = int(round((self.total_bill_amount - amount_int) * 100))

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
            return self.currency_id.amount_to_text(self.total_bill_amount)

        return ""
    def action_print_lab_bill(self):
        return self.env.ref('homeo_doctor.action_report_lab_invoice').report_action(self)
    def filter_xray_investigations(self):
        """Button action to filter X-Ray investigations"""
        self.active_investigation_type = 'xray'
        # Return action to reload the view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'doctor.lab.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_active_investigation_type': 'xray'}
        }

    def filter_mri_investigations(self):
        """Button action to filter MRI investigations"""
        self.active_investigation_type = 'mri'
        # Return action to reload the view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'doctor.lab.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_active_investigation_type': 'mri'}
        }

    def filter_lab_investigations(self):
        """Button action to filter Lab investigations (excluding X-Ray and MRI)"""
        self.active_investigation_type = 'lab'
        # Return action to reload the view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'doctor.lab.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_active_investigation_type': 'lab'}
        }

    @api.onchange('lab_billing_ids')
    def _onchange_lab_billing_ids_generate_lines(self):
        """Create lab_line_ids when lab_billing_ids are manually added or modified"""
        # Get the existing lab type IDs from lab_line_ids
        existing_lab_types = set(self.lab_line_ids.mapped('lab_type_id.id'))

        # Find newly added lab billing entries
        for billing_line in self.lab_billing_ids:
            lab_test = billing_line.lab_type_id

            # Skip if this lab type already has scan lines
            if lab_test.id in existing_lab_types:
                continue

            if lab_test:
                # Search for test configurations
                test_results = self.env['lab.resultant.confi'].search([
                    ('test_name_bill_code', '=', lab_test.id),
                    '|',
                    ('gender', '=', self.gender),
                    ('gender', '=', False)
                ])

                # Create lab scan lines for each test configuration
                for test_result in test_results:
                    self.env['lab.scan.line'].create({
                        'lab_id': self.id,
                        'lab_type_id': lab_test.id,
                        'lab_test_name': test_result.test_name,
                        'lab_reference_range': test_result.referral_range,
                        'unit': test_result.unit,
                    })

    def generate_lab_scan_lines(self):
        for record in self:
            existing_lab_types = set(record.lab_line_ids.mapped('lab_type_id.id'))

            for billing_line in record.lab_billing_ids:
                lab_test = billing_line.lab_type_id

                if lab_test.id in existing_lab_types:
                    continue

                test_results = self.env['lab.resultant.confi'].search([
                    ('test_name_bill_code', '=', lab_test.id),
                    '|',
                    ('gender', '=', record.gender),
                    ('gender', '=', False)
                ])

                for test_result in test_results:
                    self.env['lab.scan.line'].create({
                        'lab_id': record.id,
                        'lab_type_id': lab_test.id,
                        'lab_test_name': test_result.test_name,
                        'lab_reference_range': test_result.referral_range,
                        'unit': test_result.unit,
                    })
    @api.onchange('amount_paid')
    def _onchage_amount_paid(self):
        for rec in self:
            if (rec.amount_paid < rec.total_bill_amount and rec.amount_paid > 0):
                rec.balance = rec.total_bill_amount - rec.amount_paid
            elif (rec.amount_paid > rec.total_bill_amount and rec.amount_paid > 0):
                rec.balance = rec.amount_paid - rec.total_bill_amount
            else:
                rec.balance =0

    def action_sample_collected(self):

        for record in self:
            record.sample_status = 'sample_collected'
            lab_result = self.env['lab.result.page'].search([('bill_number', '=', record.id)], limit=1)

            if lab_result:
                lab_result.write({'sample_status': 'sample_collected'})


    @api.depends('lab_billing_ids')
    def _onchange_lab_billing_ids(self):
        for rec in self:
            rec.total_bill_amount = sum(rec.lab_billing_ids.mapped('total_amount'))
        # self.display_amount = self.total_bill_amount

    @api.depends('lab_line_ids')
    def _compute_grouped_lab_details(self):
        for record in self:
            grouped_data = {}
            rate_mapping = {}
            total_amount_mapping = {}

            print("line 63")

            for line in record.lab_line_ids:
                lab_type = line.lab_type_id.display_name
                print("line 67")

                if lab_type not in grouped_data:
                    grouped_data[lab_type] = []
                    rate_mapping[lab_type] = f"{line.rate_id} {line.currency_id.symbol}" if line.rate_id else "N/A"
                    total_amount_mapping[lab_type] = line.total_amount if line.total_amount else "N/A"
                    print("line 73")
                grouped_data[lab_type].append(line)
                print("line 75")

            html_content = "<table class='o_list_view table table-condensed' style='width:100%; border-collapse: collapse;'>"
            print("line 78")
            for lab_type, tests in grouped_data.items():
                print("line 80")
                # Get Rate and Total Amount for the group
                rate = rate_mapping.get(lab_type, "N/A")
                total_amount = total_amount_mapping.get(lab_type, "N/A")

                # Display Lab Type as a Header with Rate and Total Amount
                html_content += (
                    f"<tr>"
                    f"<th colspan='2' style='background-color:#dff0d8; padding: 10px;'>{lab_type}</th>"
                    f"<th colspan='1' style='background-color:#dff0d8; padding: 10px; text-align:right;'>Rate: {rate}</th>"
                    f"<th colspan='1' style='background-color:#dff0d8; padding: 10px; text-align:right;'>Total: {total_amount}</th>"
                    f"</tr>"
                )

                # Table headers for test details
                html_content += (
                    "<tr>"
                    "<th style='padding: 5px; border: 1px solid #ddd;'>Test Name</th>"
                    "<th style='padding: 5px; border: 1px solid #ddd;'>Observed Value</th>"
                    "<th style='padding: 5px; border: 1px solid #ddd;'>Reference range</th>"
                    "</tr>"
                )
                # print("line 102")
                for test in tests:
                    print("line 104")
                    html_content += (
                        f"<tr>"
                        f"<td style='padding: 5px; border: 1px solid #ddd;'>{test.lab_test_name or ''}</td>"
                        f"<td style='padding: 5px; border: 1px solid #ddd;'>{test.lab_result or ''}</td>"
                        f"<td style='padding: 5px; border: 1px solid #ddd;'>{test.lab_result or ''}</td>"
                        f"</tr>"
                    )

            html_content += "</table>"

            record.grouped_lab_details = html_content


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
                self.admitted_check = patient_reg.admission_boolean
                self.age = patient_reg.age
                self.gender = patient_reg.gender

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
        if self.staff_name and self.staff_pwd:
            employee = self.staff_name

            if not employee.staff_password_hash:
                raise ValidationError("This staff has no password set.")

            if self.staff_pwd != employee.staff_password_hash:
                raise ValidationError("The password does not match.")
        else:
            raise ValidationError("Please enter both staff name and password.")

        for rec in self:
            # Determine status based on vssc_check and mode_of_payment
            if rec.vssc_check:
                rec.status = 'paid'
            elif rec.mode_of_payment == 'credit':
                rec.status = 'unpaid'
            else:
                rec.status = 'paid'
        # self.write({
        #     'status': 'paid'
        # })

        # Calculate total amount from billing lines
        total_amount = sum(self.lab_billing_ids.mapped('total_amount'))

        # Create the lab result page record directly
        lab_result_page = self.env['lab.result.page'].create({
            'bill_number': self.id,
            'patient_id': self.user_ide.id,
            'patient_name': self.patient_name,
            'doctor': self.doctor_id.id,
            'status': 'paid',
            'patient_phone': self.patient_phone,
            'sample_collected': fields.Datetime.now(),
            'lab_collection': fields.Datetime.now(),
            'test_on': fields.Datetime.now(),
        })

        # Create lab lines for the result page
        lab_lines = []
        for lab_line in self.lab_line_ids:
            lab_lines.append((0, 0, {
                'lab_result_id': lab_result_page.id,
                'lab_type_id':lab_line.lab_type_id.id,
                'lab_test_name': lab_line.lab_test_name,
                'lab_result': lab_line.lab_result,
                'unit': lab_line.unit,
                'lab_reference_range': lab_line.lab_reference_range
            }))

        # Add the lab lines to the result page
        if lab_lines:
            lab_result_page.write({'lab_line_ids': lab_lines})

        # Return a notification message instead of opening a wizard
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Payment Confirmed',
                'message': f'Payment has been confirmed for {self.patient_name}',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
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
        if vals.get('report_reference', _('New')) == _('New'):

            seq_number = self.env['ir.sequence'].next_by_code('doctor.lab.report') or '0000'

            today = date.today()
            year_start = today.year % 100
            year_end = (today.year + 1) % 100
            fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

            vals['report_reference'] = f"{seq_number}/{fiscal_suffix}"


        self._onchange_lab_billing_ids_generate_lines()

        if vals.get('register_visible', True) and vals.get('register_patient_name'):
            # Prepare patient registration values
            patient_reg_vals = {
                'patient_id': vals.get('register_patient_name'),
                'address': vals.get('register_address'),
                'age': vals.get('register_age'),
                'email': vals.get('register_email'),
                'phone_number': vals.get('register_phone_number'),
                # 'registration_fee': vals.get('registration_fee', 50.0),
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


class LabBillingpage(models.Model):
    _name = 'lab.billing.page'
    _description = 'Lab Billing Page'

    lab_type_id = fields.Many2one('lab.investigation', string='Investigation', required=True)
    lab_billing_id = fields.Many2one('doctor.lab.report', string='Lab Test', required=True)
    test_code = fields.Char(related='lab_type_id.bill_code', string='Bill Code', store=True)

    rate_id = fields.Monetary(string='Rate', compute='_compute_rate', store=True, readonly=False)
    total_amount = fields.Monetary(string="Total", compute='_compute_total_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    @api.onchange('lab_billing_id')
    def _onchange_lab_billing_id(self):
        """Filter investigation based on active filter in parent form"""
        if self.lab_billing_id and self.lab_billing_id.active_investigation_type:
            domain = []
            if self.lab_billing_id.active_investigation_type == 'xray':
                domain = [('name', 'ilike', 'ray')]
            elif self.lab_billing_id.active_investigation_type == 'mri':
                domain = [('name', 'ilike', 'mri')]
            elif self.lab_billing_id.active_investigation_type == 'lab':
                domain = ['&', ('name', 'not ilike', 'ray'), ('name', 'not ilike', 'mri')]

            return {'domain': {'lab_type_id': domain}}
        return {}

    @api.depends('lab_type_id')
    def _compute_rate(self):
        for record in self:
            record.rate_id = record.lab_type_id.rate if record.lab_type_id else 0.0

    @api.depends('rate_id')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.rate_id


class LabScanLine(models.Model):
    _name = 'lab.scan.line'
    _description = 'Lab Scan Line'

    lab_id = fields.Many2one('doctor.lab.report', string='Lab Test')
    lab_type_id = fields.Many2one('lab.investigation', string='Investigation')
    lab_department = fields.Many2one('lab.department', string='Department')
    lab_test_name = fields.Char(string='Test Name')

    rate_id = fields.Monetary(string='Rate', compute='_compute_rate', store=True, readonly=False)
    total_amount = fields.Monetary(string="Total", compute='_compute_total_amount', store=True)
    lab_result = fields.Char('Result')
    lab_reference_range = fields.Char('Reference Range')
    lab_result_id=fields.Many2one('lab.result.page',string='Lab Result')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    unit=fields.Char(string='Unit')


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
