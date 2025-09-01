import re
from datetime import date, datetime
import logging
from gevent.util import print_run_info
from collections import defaultdict
from odoo.exceptions import UserError

import dateutil.utils
from odoo import api, fields, models, tools, _
import odoo.addons
from odoo.exceptions import ValidationError

# from odoo.odoo.exceptions import ValidationError
import base64


# from datetime import datetime, date
# default=date.today()

class PatientRegistration(models.Model):
    _name = 'patient.reg'
    _description = 'Patient Registration'
    _rec_name = 'reference_no'
    _order = 'reference_no desc,formatted_date desc'

    reference_no = fields.Char(string="Reference")
    token_no = fields.Char(string="Token No")
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date', store=True)
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
    registration_fee = fields.Many2one('patient.registration.fee', string="Registration Fee",
                                       default=lambda self: self._default_registration_fee())
    remark = fields.Text(string="Remark")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    lab_report_count = fields.Integer(string="Lab Reports", compute='_compute_lab_report_count')
    time = fields.Datetime(string="Date of Appointment")
    mri_report_ids = fields.One2many('scanning.mri', 'patient_id', string="MRI Reports")
    ct_report_ids = fields.One2many('scanning.ct', 'patient_id', string="CT Reports")
    xray_report_ids = fields.One2many('scanning.x.ray', 'patient_id', string="X-Ray Reports")
    audiology_report_ids = fields.One2many('audiology.ref', 'patient_id', string="Audiology")
    consultation_fee = fields.Integer(string='Consultation Fee', compute='_compute_consultation_fee', store=True,
                                      readonly=False)
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

    bed_id = fields.Many2one('hospital.bed', string="Bed", )
    advance_amount = fields.Integer(string='Per Day')
    # bed_id = fields.Many2one('hospital.bed', string='Bed')
    nurse_charge = fields.Float(string='Nursing Charge')
    doctor_visiting_charge = fields.Float("Doctor Charge")
    service_charge = fields.Float("Service Charge")
    alternate_no = fields.Char(string='Alternate Number')
    no_days = fields.Integer(string='Number Of Days', compute='_compute_no_days', store=True)
    admitted_date = fields.Date(string='Admitted Date')
    temp_admitted_date = fields.Datetime(string='Admitted Date')
    admission_boolean = fields.Boolean(default=False)
    dob = fields.Date(string='DOB')
    discharge_date = fields.Date(string='Discharge Date')
    temp_discharge_date = fields.Datetime(string='Discharge Date')
    vssc_boolean = fields.Boolean(string='VSSC', default=False)
    consultation_check = fields.Boolean(default=False)
    temp_reference_no = fields.Char(string=" Temporary Reference")
    no_consultation = fields.Boolean(default=True)
    walk_in = fields.Boolean(default=False)
    op_category = fields.Many2one('op.category', string='OP Category')
    doctor = fields.Many2one('doctor.profile', string='Doctor')
    block = fields.Many2one('block', string='Floor')
    new_block = fields.Many2one('hospital.block', string='Floor')
    room_number_new = fields.Many2one('hospital.room', string="Room")
    room_number = fields.Char(string="Room")
    room_transfer_date = fields.Datetime(string="Transfer Date")
    transferred_block = fields.Many2one('block', string='Floor')
    transferred_room_category = fields.Many2one('room.category', string='Room Category')
    transferred_room_number = fields.Integer(string='Room No')
    transferred_bed_number = fields.Integer(string='Bed Number')
    amount_in_advance = fields.Integer(string="Advance Amount")
    advance_mode_payment = fields.Selection([('cash', 'Cash'),
                                             ('credit', 'Credit'),
                                             ('card', 'Card'),
                                             ('cheque', 'Cheque'),
                                             ('upi', 'Mobile Pay'), ], string='Payment Method', default='cash')
    advance_remark = fields.Text(string="Remarks")
    advance_date = fields.Datetime(string="Date")
    admission_total_amount = fields.Integer(string="Total Amount", compute='_compute_total_unpaid_amount')
    temp_admission_total_amount = fields.Integer("Total Amount")
    admission_amount_paid = fields.Integer(string="Amount Paid")
    admission_balance = fields.Integer(string="Balance")
    Staff_name = fields.Many2one('hr.employee', "Staff Name")
    staff_password = fields.Char("Password")
    admit_card_no = fields.Char(string="Card No")
    admit_bank = fields.Char(string="Bank")
    rent_half = fields.Char('Rent Half Day')
    rent_full = fields.Char('Rent Full Day')
    status = fields.Selection(
        [('unpaid', 'Unpaid'), ('paid', 'Paid'), ('cancelled', 'Cancelled'), ('admitted', 'Admitted'),
         ('proceed_discharge', 'Proceed to Discharge'), ('discharged', 'Discharged')], default='unpaid')

    unpaid_general_ids = fields.One2many('general.billing', 'mrd_no' ,compute='_compute_all_totals', string="Unpaid General")
    # unpaid_lab_ids = fields.One2many('doctor.lab.report', compute='_compute_unpaid_lab', string="Unpaid Lab")
    # unpaid_pharmacy_ids = fields.One2many('pharmacy.description', compute='_compute_unpaid_pharmacy',
    #                                       string="Unpaid Pharmacy")

    paid_general_ids = fields.One2many('general.billing', 'mrd_no', string='Paid Bills',
                                       compute='_compute_all_totals')
    # unpaid_general_ids = fields.One2many('general.billing', 'mrd_no', string='Unpaid Bills',
    #                                      compute='_compute_unpaid_general')
    paid_lab_ids = fields.One2many(
        'doctor.lab.report', 'user_ide', string="Paid Lab Bills", compute='_compute_all_totals', store=False)

    unpaid_lab_ids = fields.One2many(
        'doctor.lab.report', 'user_ide', string="Unpaid Lab Bills", compute='_compute_all_totals', store=False)
    paid_lab_total = fields.Float(string="Paid Lab Total", compute='_compute_all_totals', store=False)
    unpaid_lab_total = fields.Float(string="Unpaid Lab Total", compute='_compute_all_totals', store=False)
    paid_total = fields.Float(string="Total Paid", compute="_compute_all_totals", store=True)
    unpaid_total = fields.Float(string="Total Unpaid", compute="_compute_all_totals", store=True)
    grant_total = fields.Float(string="Grand Total", compute="_compute_all_totals", store=True)
    room_rent = fields.Float(string="Room Rent", compute="_compute_total_unpaid_amount", store=True)
    paid_room_rent = fields.Float(string="Paid Room Rent", store=True)
    register_bool = fields.Boolean(default=False)
    unpaid_insurance_ids = fields.One2many(
        'ip.insurance.billing', 'mrd_no',  # use correct foreign key here!
        string="Unpaid Insurance Bills",
        compute="_compute_all_totals",
        store=False
    )

    # Total of unpaid insurance bills
    unpaid_insurance_total = fields.Float(
        string="Unpaid Insurance Total",
        compute="_compute_all_totals",
        store=False)
    unpaid_pharmacy_ids = fields.One2many(
        'pharmacy.description', 'uhid_id', string="Unpaid Pharmacy Bills", compute='_compute_all_totals',
        store=False)

    paid_pharmacy_ids = fields.One2many(
        'pharmacy.description', 'uhid_id', string="Paid Pharmacy Bills", compute='_compute_all_totals', store=False)
    paid_ip_ids = fields.Many2many(
        'ip.part.billing', string="Paid IP Bills", compute="_compute_all_totals"
    )
    unpaid_ip_ids = fields.Many2many(
        'ip.part.billing', string="Unpaid IP Bills", compute="_compute_all_totals"
    )
    referred = fields.Boolean('Referred')
    tt = fields.Boolean('TT')
    discount = fields.Integer('Discount')
    insurance_boolean = fields.Boolean(string='Insurance')

    def get_grouped_general_lines(self):
        grouped = defaultdict(lambda: {'quantity': 0, 'total_amt': 0})
        for line in self.unpaid_general_ids.mapped('general_bill_line_ids'):
            key = line.particulars.display_name
            grouped[key]['quantity'] += line.quantity or 0
            grouped[key]['total_amt'] += line.total_amt or 0
        return [{'name': k, 'quantity': v['quantity'], 'total_amt': v['total_amt']}
                for k, v in grouped.items()]
    def get_grouped_insurance_lines(self):
        grouped = defaultdict(lambda: {'quantity': 0, 'total_amt': 0})
        for line in self.unpaid_general_ids.mapped('general_bill_line_ids'):
            key = line.particulars.display_name
            grouped[key]['quantity'] += line.quantity or 0
            grouped[key]['total_amt'] += line.total_amt or 0
        return [{'name': k, 'quantity': v['quantity'], 'total_amt': v['total_amt']}
                for k, v in grouped.items()]

    @api.onchange('referred', 'tt')
    def _onchange_refferd_boolean_and_tt(self):
        for rec in self:
            if rec.referred or rec.tt:
                rec.consultation_fee = 0.0
                fee = self.env['patient.registration.fee'].search([('fee', '=', 100)], limit=1)
                if fee:
                    rec.registration_fee = fee.id
                else:
                    rec.registration_fee = self._default_registration_fee()

    def action_view_consultations(self):
        if not self.patient_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Previous Consultations',
            'res_model': 'patient.registration',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('homeo_doctor.view_patient_registration_tree').id, 'tree'),
                (self.env.ref('homeo_doctor.patient_registration_form').id, 'form'),
            ],
            'domain': [('patient_id', '=', self.reference_no)],
            'context': {'default_patient_id': self.reference_no},
            'target': 'new',
        }

    def cancel_appointment(self):

        """Cancel the appointment and only the specific related patient registration record"""

        self.status = "cancelled"

        # Find only the specific related patient.registration record for this appointment

        # by matching both user_id and patient_id with the current record's id

        related_registration = self.env['patient.registration'].search([

            ('user_id', '=', self.id),

            ('patient_id', '=', self.id),

            ('status', 'in', ['confirmed', 'completed'])

        ], limit=1)

        if related_registration:
            related_registration.write({'status': 'cancelled'})

    # @api.depends('reference_no')
    # def _compute_unpaid_general(self):
    #     for rec in self:
    #         rec.unpaid_general_ids = self.env['general.billing'].search([
    #             ('mrd_no', '=', rec.id),
    #             ('status', '!=', 'paid')
    #         ])
    @api.depends('reference_no', 'admitted_date', 'vssc_boolean')
    def _compute_all_totals(self):
        today = fields.Date.today()
        # print(today, 'todaytodaytodaytodaytodaytodaytodaytodaytodaytodaytodaytodaytodaytodaytoday')
        for rec in self:
            # Initialize
            rec.paid_total = 0.0
            rec.unpaid_total = 0.0
            rec.grant_total = 0.0
            rec.paid_lab_total = 0.0
            rec.unpaid_lab_total = 0.0
            paid_general = 0.0
            unpaid_general = 0.0
            rec.unpaid_insurance_total = 0.0
            today = fields.Date.today()
            # -----------------------------
            # General Billing
            # -----------------------------
            if rec.admitted_date:
                today = fields.Date.today()
                paid_general = self.env['general.billing'].search([
                    ('mrd_no', '=', rec.id),
                    ('status', '=', 'paid'),
                    ('bill_date', '>=', rec.admitted_date),
                    ('bill_date', '<=', fields.Date.today()),
                ])
                unpaid_general = self.env['general.billing'].search([
                    ('mrd_no', '=', rec.id),
                    ('status', '!=', 'paid'),
                    ('bill_date', '>=', rec.admitted_date),
                    ('bill_date', '<=', fields.Date.today()),
                ])
                rec.paid_general_ids = paid_general
                rec.unpaid_general_ids = unpaid_general
            # paid_insurance = self.env['ip.insurance.billing'].search([
            #     ('patient_id', '=', rec.id),
            #     ('state', '=', 'paid'),
            #     ('bill_date', '>=', rec.admitted_date),
            #     ('bill_date', '<=', today),
            # ])
            unpaid_insurance = self.env['ip.insurance.billing'].search([
                ('mrd_no', '=', rec.id),
                ('status', '!=', 'paid'),
                ('bill_date', '>=', rec.admitted_date),
                ('bill_date', '<=', today),
            ])

            # rec.paid_insurance_ids = paid_insurance
            rec.unpaid_insurance_ids = unpaid_insurance
            # rec.paid_insurance_total = sum(b.total_amount or 0.0 for b in paid_insurance)
            rec.unpaid_insurance_total = sum(b.total_amount or 0.0 for b in unpaid_insurance)
            # -----------------------------
            # Pharmacy Billing
            # -----------------------------
            paid_pharmacy = self.env['pharmacy.description'].search([
                ('uhid_id', '=', rec.id),
                ('status', '=', 'paid'),
                ('date', '>=', rec.admitted_date),
                ('date', '<=', today),
            ])
            unpaid_pharmacy = self.env['pharmacy.description'].search([
                ('uhid_id', '=', rec.id),
                ('status', '=', 'unpaid'),
                ('date', '>=', rec.admitted_date),
                ('date', '<=', today),
            ])
            rec.paid_pharmacy_ids = paid_pharmacy
            rec.unpaid_pharmacy_ids = unpaid_pharmacy
            paid_ip = self.env['ip.part.billing'].search([
                ('mrd_no', '=', rec.id),
                ('status', '=', 'paid'),
                ('bill_date', '>=', rec.admitted_date),
                ('bill_date', '<=', today),
            ])
            unpaid_ip = self.env['ip.part.billing'].search([
                ('mrd_no', '=', rec.id),
                ('status', '=', 'unpaid'),
                ('bill_date', '>=', rec.admitted_date),
                ('bill_date', '<=', today),
            ])
            rec.paid_ip_ids = paid_ip
            rec.unpaid_ip_ids = unpaid_ip
            # -----------------------------
            # Lab Billing (Both Paid & Unpaid)
            # -----------------------------
            paid_lab = self.env['doctor.lab.report'].search([
                ('user_ide', '=', rec.id),
                ('status', '=', 'paid'),
                ('date', '>=', rec.admitted_date),
                ('date', '<=', today),
            ])
            if not rec.vssc_boolean:
                unpaid_lab = self.env['doctor.lab.report'].search([
                    ('user_ide', '=', rec.id),
                    ('status', '=', 'unpaid'),
                    ('mode_of_payment', '=', 'credit'),
                    ('date', '>=', rec.admitted_date),
                    ('date', '<=', today),
                ])
            else:
                unpaid_lab = self.env['doctor.lab.report'].search([
                    ('user_ide', '=', rec.id),
                    '|',
                    ('status', '!=', 'paid'),
                    '&',
                    ('status', '=', 'paid'),
                    ('mode_of_payment', '=', 'credit'),
                    ('status', '!=', 'credit'),
                    ('date', '>=', rec.admitted_date),
                    ('date', '<=', today),
                ])

            rec.paid_lab_ids = paid_lab
            rec.unpaid_lab_ids = unpaid_lab
            rec.paid_lab_total = sum(l.total_bill_amount for l in paid_lab)
            rec.unpaid_lab_total = sum(l.total_bill_amount for l in unpaid_lab)

            # -----------------------------
            # Totals
            # -----------------------------
            rec.paid_total = (
                    sum(p.total_amount or 0.0 for p in rec.paid_general_ids) +
                    sum(p.total_amount or 0.0 for p in rec.paid_pharmacy_ids) +
                    sum(p.total_amount or 0.0 for p in rec.paid_ip_ids) -
                    sum(p.room_rent_total or 0.0 for p in rec.paid_ip_ids) +
                    rec.paid_lab_total
            )

            rec.unpaid_total = (
                    sum(u.total_amount or 0.0 for u in rec.unpaid_general_ids) +
                    sum(u.total_amount or 0.0 for u in rec.unpaid_pharmacy_ids) +
                    sum(u.total_amount or 0.0 for u in rec.unpaid_ip_ids) +
                    rec.unpaid_lab_total +  rec.unpaid_insurance_total
            )

            rec.grant_total = rec.paid_total + rec.unpaid_total + (rec.room_rent or 0.0)
            rec.paid_room_rent = sum(p.room_rent_total or 0.0 for p in rec.paid_ip_ids)

    # @api.depends('reference_no')
    # def _compute_unpaid_general(self):
    #     for rec in self:
    #         rec.paid_general_ids = False
    #         rec.unpaid_general_ids = False
    #         rec.paid_total = 0.0
    #         rec.unpaid_total = 0.0
    #         rec.grant_total = 0.0
    #
    #         if rec.admitted_date:
    #             today = fields.Date.today()
    #
    #             paid_bills = self.env['general.billing'].search([
    #                 ('mrd_no', '=', rec.id),
    #                 ('status', '=', 'paid'),
    #                 ('bill_date', '>=', rec.admitted_date),
    #                 ('bill_date', '<=', today),
    #             ])
    #
    #             unpaid_bills = self.env['general.billing'].search([
    #                 ('mrd_no', '=', rec.id),
    #                 ('status', '!=', 'paid'),
    #                 ('bill_date', '>=', rec.admitted_date),
    #                 ('bill_date', '<=', today),
    #             ])
    #
    #             rec.paid_general_ids = paid_bills
    #             rec.unpaid_general_ids = unpaid_bills
    #
    #             rec.paid_total = sum(p.total_amount for p in paid_bills)
    #             rec.unpaid_total = sum(u.total_amount for u in unpaid_bills)
    #             rec.grant_total= rec.grant_total = rec.paid_total + rec.unpaid_total + rec.room_rent

    @api.depends('reference_no', 'vssc_boolean')
    def _compute_unpaid_lab(self):
        for rec in self:
            # base_domain = [('user_ide', '=', rec.id)]

            if not rec.vssc_boolean:
                # Show only status unpaid and paid
                # print("vssc boolean not")
                status_domain = [
                    ('user_ide', '=', rec.id),
                    ('status', '=', 'unpaid'),
                    ('mode_of_payment', '=', 'credit'),
                ]
            else:
                # print("vssc boolean yes")
                # Show only unpaid (including credit payments that are not credited)
                status_domain = [
                    ('user_ide', '=', rec.id),
                    '|',
                    ('status', '!=', 'paid'),
                    '&',
                    ('status', '=', 'paid'),
                    ('mode_of_payment', '=', 'credit'),
                    ('status', '!=', 'credit')
                ]

            final_domain = status_domain
            rec.unpaid_lab_ids = self.env['doctor.lab.report'].search(final_domain)

    register_total_amount = fields.Integer(string="Total Amount", compute="_compute_register_total")
    register_amount_paid = fields.Integer(string="Amount Paid")
    register_balance = fields.Integer(string="Balance")
    register_staff_name = fields.Many2one('hr.employee', "Staff Name")
    register_staff_password = fields.Char("Password")
    register_mode_payment = fields.Selection([('cash', 'Cash'),
                                              ('card', 'Card'),
                                              ('cheque', 'Cheque'),
                                              ('credit', 'Credit'),
                                              ('upi', 'Mobile Pay'), ], string='Payment Method', default='cash')
    register_card_no = fields.Char(string="Card No")
    register_bank_name = fields.Char(string="Bank")

    # @api.onchange('doctor_visiting_charge','service_charge','nurse_charge')
    # def charges_add(self):
    #     for rec in self:
    #         rec.admission_total_amount = rec.admission_total_amount + rec.doctor_visiting_charge + rec.service_charge + rec.nurse_charge
    @api.onchange('nurse_charge', 'doctor_visiting_charge', 'service_charge')
    def _onchange_charges(self):
        """Calculate total amount when charge fields change"""
        # Manually trigger the computation for immediate UI feedback
        self._compute_total_unpaid_amount()

    def admit_reception(self):
        self.admission_boolean = True
        self.status = 'admitted'

    @api.onchange('register_amount_paid')
    def _onchange_register_amount_paid(self):
        for rec in self:
            total = rec.register_total_amount
            paid = rec.register_amount_paid
            # rec.register_balance = total - paid
            # print(total, "total....")
            # print(paid, "paid....")
            # print(rec.register_balance, "balance....")
            if (paid < total and paid > 0):
                rec.register_balance = total - paid
            elif (paid > total and paid > 0):
                rec.register_balance = paid - total
            else:
                rec.register_balance = 0

    @api.depends('vssc_boolean', 'doc_name')
    def _compute_consultation_fee(self):
        for rec in self:
            if rec.vssc_boolean:
                rec.consultation_fee = 400
            else:
                # You might want to add your logic here for non-VSSC patients
                # For now, I'm leaving it as is (presumably set by another method)
                rec.consultation_fee = 0  # or whatever default you want

    @api.depends('vssc_boolean')
    def _default_registration_fee(self):
        # Return false/None if VSSC, otherwise return your default registration fee
        if self.vssc_boolean:
            return False
        else:
            # Return your default registration fee record
            registration_fee = self.env['patient.registration.fee'].search([], limit=1)
            return registration_fee.id if registration_fee else False

    @api.onchange('vssc_boolean')
    def _onchange_vssc_boolean(self):
        for rec in self:
            if rec.vssc_boolean:
                rec.registration_fee = False  # Set to None/False when VSSC is True
                rec.consultation_fee = 400
            else:
                # Reset to default registration fee
                default_fee = self._default_registration_fee()
                rec.registration_fee = default_fee
                # Reset consultation fee if needed
                # rec.consultation_fee = 0  # or compute based on your business logic

    @api.onchange('registration_fee', 'consultation_fee', 'vssc_boolean')
    def _onchange_total_amount(self):
        for rec in self:
            if rec.vssc_boolean:
                rec.register_total_amount = 400  # Only consultation fee for VSSC
            else:
                reg_fee = rec.registration_fee.fee if rec.registration_fee else 0
                rec.register_total_amount = reg_fee + (rec.consultation_fee or 0)

    @api.depends('registration_fee', 'consultation_fee', 'vssc_boolean')
    def _compute_register_total(self):
        for rec in self:
            if rec.vssc_boolean:
                rec.register_total_amount = 400  # Only consultation fee for VSSC
            else:
                reg_fee = rec.registration_fee.fee if rec.registration_fee else 0
                rec.register_total_amount = reg_fee + (rec.consultation_fee or 0)

    # @api.depends('reference_no', 'admitted_date')
    # def _compute_unpaid_pharmacy(self):
    #     today = fields.Date.today()
    #     unpaid_total=0
    #     for rec in self:
    #         domain = [
    #             ('uhid_id', '=', rec.id),
    #             ('status', '=', 'unpaid'),
    #         ]
    #         if rec.admitted_date:
    #             domain.append(('date', '>=', rec.admitted_date))
    #             domain.append(('date', '<=', today))
    #
    #         rec.unpaid_pharmacy_ids = self.env['pharmacy.description'].search(domain)
    #         rec.grant_total += sum(line.total_amount for line in rec.unpaid_pharmacy_ids)
    #         rec.unpaid_total += sum(u.total_amount for u in  rec.unpaid_pharmacy_ids)
    #
    # @api.depends('reference_no', 'admitted_date')
    # def _compute_paid_pharmacy(self):
    #     today = fields.Date.today()
    #     paid_total=0
    #     for rec in self:
    #         domain = [
    #             ('uhid_id', '=', rec.id),
    #             ('status', '=', 'paid'),
    #         ]
    #         if rec.admitted_date:
    #             domain.append(('date', '>=', rec.admitted_date))
    #             domain.append(('date', '<=', today))
    #
    #         rec.paid_pharmacy_ids = self.env['pharmacy.description'].search(domain)
    #         rec.grant_total += sum(line.total_amount for line in rec.paid_pharmacy_ids)
    #         rec.paid_total += sum(p.total_amount for p in rec.paid_pharmacy_ids)
    #         print(rec.paid_total,'paid_totalpaid_totalpaid_totalpaid_totalpaid_totalpaid_totalpaid_totalpaid_totalpaid_totalpaid_totalpaid_totalpaid_total.................')

    # @api.depends('unpaid_general_ids', 'unpaid_lab_ids', 'unpaid_pharmacy_ids', 'admitted_date', 'discharge_date',
    #              'rent_half', 'rent_full')
    # def _compute_total_unpaid_amount(self):
    #     for rec in self:
    #         total = 0.0
    #         full_days = 0
    #         rent_full_value = 0
    #         remaining_hours = 0
    #         # Calculate service totals
    #         for general in rec.unpaid_general_ids:
    #             total += general.total_amount or 0.0
    #
    #         for lab in rec.unpaid_lab_ids:
    #             total += lab.total_bill_amount or 0.0
    #
    #         for pharmacy in rec.unpaid_pharmacy_ids:
    #             total += pharmacy.total_amount or 0.0
    #
    #         # Calculate rent if discharge date is present
    #         if rec.admitted_date and rec.discharge_date:
    #             # Convert to datetime objects if they're not already
    #             admitted = fields.Datetime.from_string(rec.admitted_date) if isinstance(rec.admitted_date,
    #                                                                                     str) else rec.admitted_date
    #             discharge = fields.Datetime.from_string(rec.discharge_date) if isinstance(rec.discharge_date,
    #                                                                                       str) else rec.discharge_date
    #
    #             # Calculate the duration in days (including partial days)
    #             duration_hours = (discharge - admitted).total_seconds() / 3600
    #
    #             # Calculate full days and remaining hours
    #             full_days = int(duration_hours / 24)
    #             remaining_hours = duration_hours % 24
    #
    #             # Add full day rent - convert Char field to float for calculation
    #             rent_full_value = float(rec.rent_full or 0) if rec.rent_full and rec.rent_full.strip() else 0
    #             total += full_days * rent_full_value -(rec.paid_room_rent)
    #
    #             # Add half day rent if remaining hours > 0
    #             if remaining_hours > 0:
    #                 rent_half_value = float(rec.rent_half or 0) if rec.rent_half and rec.rent_half.strip() else 0
    #                 total += rent_half_value
    #
    #         total += (rec.nurse_charge or 0) + (rec.doctor_visiting_charge or 0) + (rec.service_charge or 0)
    #
    #         rec.admission_total_amount = total
    #         rec.room_rent = full_days * rent_full_value + (rent_half_value if remaining_hours > 0 else 0.0)
    @api.depends('unpaid_general_ids', 'unpaid_lab_ids', 'unpaid_pharmacy_ids', 'admitted_date', 'discharge_date',
                 'rent_full')
    def _compute_total_unpaid_amount(self):
        for rec in self:
            total = 0.0
            full_days = 0
            rent_full_value = 0

            # Calculate service totals
            for general in rec.unpaid_general_ids:
                total += general.total_amount or 0.0

            for lab in rec.unpaid_lab_ids:
                total += lab.total_bill_amount or 0.0

            for pharmacy in rec.unpaid_pharmacy_ids:
                total += pharmacy.total_amount or 0.0

            # Calculate rent only based on full days
            if rec.admitted_date and rec.discharge_date:
                admitted = fields.Date.from_string(rec.admitted_date) if isinstance(rec.admitted_date,
                                                                                    str) else rec.admitted_date
                discharge = fields.Date.from_string(rec.discharge_date) if isinstance(rec.discharge_date,
                                                                                      str) else rec.discharge_date

                # Get difference in days (no hours)
                full_days = (discharge - admitted).days

                # Add full day rent (char to float)
                rent_full_value = float(rec.rent_full or 0) if rec.rent_full and str(rec.rent_full).strip() else 0
                total += (full_days * rent_full_value) - (rec.paid_room_rent or 0)

            # Add other charges
            total += (rec.nurse_charge * full_days or 0) + (rec.doctor_visiting_charge * full_days or 0) + (
                        rec.service_charge * (full_days + 1) or 0)

            # Assign final values
            rec.admission_total_amount = total
            rec.room_rent = full_days * rent_full_value

    discharge_bill_number = fields.Char(
        string="Discharge Bill #",
        readonly=True,
        copy=False,
        default='/'
    )

    def write(self, vals):
        res = super(PatientRegistration, self).write(vals)
        for record in self:
            if 'admitted_date' in vals and vals.get('admitted_date'):
                record.discharge_bill_number = record._generate_bill_number(record.admitted_date)
        return res

    def _generate_bill_number(self, admitted_date):
        raw_seq = self.env['ir.sequence'].next_by_code('discharge.bill') or '0'
        padded_seq = str(raw_seq).zfill(4)

        # if admitted_date is empty, use today's date
        today = admitted_date or date.today()
        year_start = today.year % 100
        year_end = (today.year + 1) % 100
        fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

        return f"{padded_seq}/{fiscal_suffix}"

    def action_discharged_patient_reg(self):
        if self.Staff_name and self.staff_password:
            employee = self.Staff_name

            if not employee.staff_password_hash:
                raise ValidationError("This staff has no password set.")

            if self.staff_password != employee.staff_password_hash:
                raise ValidationError("The password does not match.")
        else:
            raise ValidationError("Please enter both staff name and password.")
        for record in self:
            record.status = 'discharged'
            # record.admission_boolean = False
            record.temp_admission_total_amount = record.admission_total_amount
            record.temp_admitted_date = record.admitted_date
            record.temp_discharge_date = record.discharge_date

            # Mark the room as available
            if record.room_number_new:
                record.room_number_new.is_available = False

            admitted_patient = self.env['hospital.admitted.patient'].search([('patient_id', '=', record.id)], limit=1)
            if not record.discharge_bill_number or record.discharge_bill_number == '/':
                # a) grab next sequence (must exist in Settings → Technical → Sequences)
                raw_seq = self.env['ir.sequence'].next_by_code('discharge.bill') or '0'
                padded_seq = str(raw_seq).zfill(4)

                # b) compute fiscal year suffix: e.g. if today is July 2025 ⇒ "25-26"
                today = date.today()
                year_start = today.year % 100
                year_end = (today.year + 1) % 100
                fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

                # c) assign it
                record.discharge_bill_number = f"{padded_seq}/{fiscal_suffix}"
            if admitted_patient:
                admitted_patient.status = 'discharged'
                rec = self.env['discharged.patient.record'].create({
                    'patient_id': record.reference_no,
                    'name': record.patient_id,
                    'discharge_date': record.discharge_date,
                    'admitted_date': record.admitted_date,
                    'room_number': record.room_number_new.id,
                    'doctor': record.doctor.id,
                    'total_amount': record.admission_total_amount,
                    'room_category_new': record.room_category_new.id,
                    'new_block': record.new_block.id,
                    'bed_id': record.bed_id.id,
                    'amount_in_advance': record.amount_in_advance,
                    'bystander_name': record.bystander_name,
                    'relation': record.bystander_relation,
                    'email': record.bystander_email,
                    'bystander_mobile': record.bystander_mobile,
                    'alternate_no': record.alternate_no,
                    'op_category': record.op_category.id,
                    'pay_mode': record.advance_mode_payment,

                })

                report = self.env.ref('homeo_doctor.action_report_discharge_challan')
                pdf_content, _ = report._render_qweb_pdf(self.ids)
                pdf_base64 = base64.b64encode(pdf_content)

                rec.write({
                    'discharge_pdf': pdf_base64,
                    'file_name': f"Discharge_{record.discharge_bill_number}.pdf"
                })

                # ✅ Return PDF as usual
                # return report.report_action(self)
                # record.unpaid_general_ids.write({'status': 'paid'})
                # if record.vssc_boolean:
                #     record.unpaid_lab_ids.write({'status': 'credit'})
                #     record.paid_lab_ids.write({'status': 'credit'})
                # else:
                #     record.unpaid_lab_ids.write({'status': 'paid'})
                # record.unpaid_pharmacy_ids.write({'status': 'paid'})
        return self.env.ref('homeo_doctor.action_report_discharge_challan').report_action(self)

    def consolidated_bill(self):
        self.action_discharged_patient_reg()
        return self.env.ref('homeo_doctor.action_report_consolidated_discharge_challan').report_action(self)
    def insurance_bill(self):
        self.action_discharged_patient_reg()
        return self.env.ref('homeo_doctor.action_report_insurance_challan').report_action(self)

    def finalize_discharge_cleanup(self):
        for record in self:
            record.unpaid_general_ids.write({'status': 'paid'})
            if record.vssc_boolean:
                record.unpaid_lab_ids.write({'status': 'credit'})
                record.paid_lab_ids.write({'status': 'credit'})
            else:
                record.unpaid_lab_ids.write({'status': 'paid'})
            record.unpaid_pharmacy_ids.write({'status': 'paid'})
            record.admission_boolean = False
            record.update({
                'room_number_new': False,
                'bed_id': False,
                'admitted_date': False,
                'discharge_date': False,
                'room_category_new': False,
                'bystander_name': False,
                'bystander_mobile': False,
                'bystander_relation': False,
                'bystander_email': False,
                'rent_full': False,
                'rent_half': False,
                'doctor': False,
                'new_block': False,
                'alternate_no': False,
                'amount_in_advance': False,
                'op_category': False,
                'admission_total_amount': False,
                'nurse_charge': False,
                'doctor_visiting_charge': False,
                'service_charge': False,
                'Staff_name': False,
                'staff_password': False,
                'insurance_boolean': False,

            })

        return

    @api.onchange('room_category_new')
    def _onchange_room_category_new(self):
        if self.room_category_new:
            # Filter rooms by the selected room category
            return {
                'domain': {
                    'room_number_new': [('room_type_new', '=', self.room_category_new.id), ('is_available', '=', False)]
                }
            }
        return {'domain': {'room_number_new': []}}

    @api.onchange('room_number_new')
    def _onchange_room_number(self):
        if self.room_number_new:
            self.bed_id = self.room_number_new.bed_number_new
            self.new_block = self.room_number_new.block_new
            self.rent_half = self.room_number_new.rent_half
            self.rent_full = self.room_number_new.rent_full
        else:
            self.bed_id = False
            self.new_block = False

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

    bill_number = fields.Char(string="Bill Number", readonly=True, copy=False, default='/')

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

    def action_register_pay(self):
        self.ensure_one()

        if self.register_staff_name and self.register_staff_password:
            employee = self.register_staff_name

            if not employee.staff_password_hash:
                raise ValidationError("This staff has no password set.")

            if self.register_staff_password != employee.staff_password_hash:
                raise ValidationError("The password does not match.")
        else:
            raise ValidationError("Please enter both staff name and password.")

        if not self.bill_number or self.bill_number == '/':
            raw_seq = self.env['ir.sequence'].next_by_code('patient.bill') or '0'
            padded_seq = str(raw_seq).zfill(4)

            today = date.today()
            year_start = today.year % 100
            year_end = (today.year + 1) % 100
            fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

            self.bill_number = f"{padded_seq}/{fiscal_suffix}"

        self.status = 'paid'
        self.register_bool = True

        if self.vssc_boolean and self.consultation_fee != 400:
            self.consultation_fee = 400

        self.register_staff_name = False
        self.register_staff_password = False

        return self.env.ref('homeo_doctor.report_patient_challan_action').report_action(self)

    admitted_bill_number = fields.Char(string="Bill Number", readonly=True, copy=False, default='/')

    def action_create_admission(self):
        if self.Staff_name and self.staff_password:
            employee = self.Staff_name

            if not employee.staff_password_hash:
                raise ValidationError("This staff has no password set.")

            if self.staff_password != employee.staff_password_hash:
                raise ValidationError("The password does not match.")
        else:
            raise ValidationError("Please enter both staff name and password.")
        if not self.admitted_bill_number or self.admitted_bill_number == '/':
            raw_seq = self.env['ir.sequence'].next_by_code('admitted.bill') or '0'
            padded_seq = str(raw_seq).zfill(4)

            today = date.today()
            year_start = today.year % 100
            year_end = (today.year + 1) % 100
            fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

            self.admitted_bill_number = f"{padded_seq}/{fiscal_suffix}"
        admission_model = self.env['hospital.admitted.patient']
        registration_model = self.env['patient.reg']
        room_model = self.env['hospital.room']
        advance_model = self.env['advance.patient.record']
        for rec in self:
            rec.admission_total_amount = False
            patient = registration_model.search([('reference_no', '=', rec.reference_no)], limit=1)
            if not patient:
                raise UserError(f"No patient found with reference no: {rec.reference_no}")

            admission_model.create({
                'patient_id': patient.id,
                'admission_date': fields.Datetime.now(),
                'room_number': rec.room_number_new.id,
                'room_category_new': rec.room_category_new.id,
                'bed_id': rec.bed_id.id,
                'attending_doctor': rec.doctor.id,
            })
            advance_model.create({
                'patient_id': rec.reference_no,
                'name': rec.patient_id,
                'discharge_date': rec.discharge_date,
                'admitted_date': rec.admitted_date,
                'room_number': rec.room_number_new.id,
                'doctor': rec.doctor.id,
                'total_amount': rec.admission_total_amount,
                'room_category_new': rec.room_category_new.id,
                'new_block': rec.new_block.id,
                'bed_id': rec.bed_id.id,
                'amount_in_advance': rec.amount_in_advance,
                'bystander_name': rec.bystander_name,
                'relation': rec.bystander_relation,
                'email': rec.bystander_email,
                'bystander_mobile': rec.bystander_mobile,
                'alternate_no': rec.alternate_no,
                'op_category': rec.op_category.id,
                'pay_mode': rec.advance_mode_payment,

            })

            if rec.room_number_new:
                room = room_model.browse(rec.room_number_new.id)
                if room:
                    room.write({'is_available': True})
        return self.env.ref('homeo_doctor.action_report_admission_challan').report_action(self)

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

    @api.depends('discharge_date', 'admitted_date')
    def _compute_no_days(self):
        for record in self:
            if record.admitted_date:
                admitted_date = fields.Datetime.to_datetime(record.admitted_date).date()
                current_date = fields.Datetime.to_datetime(
                    record.discharge_date).date() if record.discharge_date else fields.Date.today()
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

    @api.depends('doc_name', 'referred', 'tt', 'vssc_boolean')
    def _compute_consultation_fee(self):
        for record in self:
            if record.doc_name:
                if record.vssc_boolean:
                    record.register_total_amount = 400

                else:
                    # Automatically populate consultation_fee from the selected doctor's record
                    record.consultation_fee = record.doc_name.consultation_fee_doctor
                if record.doc_name:
                    if record.referred or record.tt:
                        record.consultation_fee = 0
                        # Set registration_fee to the one with fee = 100
                        fee = self.env['patient.registration.fee'].search([('fee', '=', 100)], limit=1)
                        record.registration_fee = fee.id if fee else record._default_registration_fee()
                    else:
                        # Normal case: use doctor's consultation fee and default reg fee
                        record.consultation_fee = record.doc_name.consultation_fee_doctor
                        record.registration_fee = record._default_registration_fee()

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
                'doctor': record.doc_name.id,
                'appointment_date': record.time,
            })

        return record

    @api.depends('date', 'time')
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
    _name = 'patient.registration.fee'
    _rec_name = 'fee'

    fee = fields.Integer(string='Patient Registration Fee')


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
