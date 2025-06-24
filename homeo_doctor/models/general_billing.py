from num2words import num2words

from odoo import models, fields, api
from datetime import datetime

# from odoo.odoo.tools.safe_eval import dateutil

from datetime import datetime

# from odoo.odoo.exceptions import UserError


# from odoo.odoo.exceptions import UserError


# from odoo.odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class GeneralBilling(models.Model):
    _name = 'general.billing'
    _description = 'General Billing'
    _rec_name = 'bill_number'
    _order = 'bill_number desc'

    bill_number = fields.Char(string='Bill Number',  copy=False, default='New')
    mrd_no = fields.Many2one('patient.reg', string='UHID')
    patient_name = fields.Char(string='Patient Name')
    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    mobile = fields.Char(string='Mobile')
    bill_date = fields.Datetime(string='Bill Date',default=lambda self: datetime.today())
    op_category = fields.Many2one('op.category', string='OP Category')
    doctor = fields.Many2one('doctor.profile', string='Doctor')
    department = fields.Many2one('general.department', string='Department')
    particulars = fields.Many2one('general.dept.costing', string='Select Particulars')
    bill_type = fields.Many2one('bill.type', string='Bill Type')

    ip_no = fields.Char(string='IP No')
    general_bill_line_ids = fields.One2many('general.bill.line','bill_line_id')
    total_item=fields.Char(string='Total Item',compute="_compute_totals")
    total_qty=fields.Char(string='Total Qty',compute="_compute_totals")
    total_tax=fields.Char(string='Total Tax')
    total_amount = fields.Integer(string='Total Amount')
    discount_type =fields.Selection([('amount','Amount'),('percentage','Percentage')],default='percentage')
    discount = fields.Integer(string='Discount')
    oc_type=fields.Selection([('amount','Amount'),('percentage','Percentage')],default='amount',string='O.C Type')
    oc=fields.Integer(string='O.C')
    reference=fields.Selection([('no','No'),('yes','YES')],default='no',string='Reference')
    mode_pay=fields.Selection([('cash', 'Cash'),
                                ('credit', 'Credit'),
                                ('card', 'Card'),
                                ('cheque', 'Cheque'),
                                ('upi', 'UPI'),], string='Payment Method',default='cash')
    net_amount=fields.Integer(string='Net Bill Amount')
    bill_by=fields.Char(string='Bill By')
    remarks =fields.Char(string='Remarks')
    staff_pwd=fields.Char(string='Staff Password')
    staff_name=fields.Many2one('hr.employee',string='Staff Name')
    amount_paid = fields.Integer(string="Amount Paid")
    balance = fields.Integer(string="Balance")
    status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('observation','Observation'),
        ('discharge','Discharge'),
    ], string="Status", default="unpaid", tracking=True)

    amount_in_words = fields.Char("Total in Words", compute="_compute_amount_in_words")
    discount_amount = fields.Integer(string="Discount amount")
    rent = fields.Integer(string="Rent",Default=0)
    observation = fields.Boolean(string="Observation")
    observation_status = fields.Selection([
                          ('observation', 'Observation'),
                          ('discharge','Discharge')
                          ], string="Status")
    vssc_boolean=fields.Boolean(string='VSSC')
    def action_observation(self):
        """Method to toggle observation field when Observation button is clicked"""
        self.observation = True
        # If observation is True, set observation_status to 'observation'
        if self.observation:
            self.observation_status = 'observation'
            self.status = 'observation'

    def action_observation_discharge(self):
        self.observation = False
        self.status = 'discharge'
        if self.observation:
            self.observation_status = 'discharge'



    @api.onchange('discount', 'discount_type', 'total_amount')
    def _onchange_discount(self):
        """Calculate discount amount and net payable amount based on discount"""
        if self.total_amount:
            if self.discount_type == 'percentage' and self.discount:
                self.discount_amount = (self.total_amount * self.discount) / 100
            elif self.discount_type == 'amount' and self.discount:
                self.discount_amount = self.discount
            else:
                self.discount_amount = 0

            # Calculate net amount (payable amount after discount)
            self.net_amount = self.total_amount - self.discount_amount

    # def action_create_admission(self):
    #     admitted_any = False
    #     warnings = []
    #
    #     for rec in self:
    #         if not rec.mrd_no:
    #             continue
    #
    #         patient = rec.mrd_no  # patient.reg record
    #
    #         if patient.status != 'admitted' and not patient.admission_boolean:
    #             patient.admission_boolean = True
    #             patient.status = 'admitted'
    #             admitted_any = True
    #         else:
    #             warnings.append(f"Patient {patient.patient_id or patient.id} is already admitted.")
    #
    #     if warnings:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Warning',
    #                 'message': '\n'.join(warnings),
    #                 'sticky': True,
    #                 'type': 'warning',
    #             }
    #         }
    #
    #     if not admitted_any:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Info',
    #                 'message': 'No valid billing records with UHID found for admission.',
    #                 'sticky': True,
    #                 'type': 'info',
    #             }
    #         }
    #
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Success',
    #             'message': 'Admission created successfully.',
    #             'sticky': False,
    #             'type': 'success',
    #         }
    #     }
    def action_create_admission(self):
        admitted_any = False
        warnings = []

        for rec in self:
            if not rec.mrd_no:
             
                vals = {
                    'patient_id': rec.patient_name or 'Unknown',
                    'age': rec.age,
                    'gender': rec.gender,
                    'phone_number': rec.mobile,

                }


                patient = self.env['patient.reg'].create(vals)
                rec.mrd_no = patient
            else:
                patient = rec.mrd_no

            if patient.status != 'admitted' and not patient.admission_boolean:
                patient.admission_boolean = True
                patient.status = 'admitted'
                admitted_any = True
            else:
                warnings.append(f"Patient {patient.patient_id or patient.id} is already admitted.")

        if warnings:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': '\n'.join(warnings),
                    'sticky': True,
                    'type': 'warning',
                }
            }

        if not admitted_any:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': 'No valid billing records with UHID found for admission.',
                    'sticky': True,
                    'type': 'info',
                }
            }

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

    @api.onchange('amount_paid')
    def onchange_amount_paid(self):
        for rec in self:
            if (rec.amount_paid < rec.net_amount and rec.amount_paid > 0):
                rec.balance = rec.net_amount - rec.amount_paid
            elif (rec.amount_paid > rec.net_amount and rec.amount_paid > 0):
                rec.balance = rec.amount_paid - rec.net_amount
            else:
                rec.balance =0


    @api.depends('total_amount')
    def _compute_amount_in_words(self):
        for record in self:
            record.amount_in_words = num2words(record.total_amount, lang='en').title() + " Only"

    def action_pay_button(self):
        if self.staff_name and self.staff_pwd:
            employee = self.staff_name

            if not employee.staff_password_hash:
                raise ValidationError("This staff has no password set.")

            if self.staff_pwd != employee.staff_password_hash:
                raise ValidationError("The password does not match.")
        else:
            raise ValidationError("Please enter both staff name and password.")
        for record in self:
            record.status = 'paid'
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

    @api.depends('general_bill_line_ids.quantity', 'general_bill_line_ids.total_amt', 'general_bill_line_ids.tax','rent')
    def _compute_totals(self):
        for record in self:
            record.total_item = len(record.general_bill_line_ids)
            record.total_qty = sum(record.general_bill_line_ids.mapped('quantity'))
            record.total_amount = sum(record.general_bill_line_ids.mapped('total_amt')) + record.rent

            record.total_tax = sum(
                line.tax.tax * line.total_amt / 100 for line in record.general_bill_line_ids if line.tax)

            record.net_amount = sum(record.general_bill_line_ids.mapped('total_amt'))+ record.rent

    @api.onchange('mrd_no')
    def _onchange_mrd_no(self):
        if self.mrd_no:
            self.patient_name = self.mrd_no.patient_id
            self.age = self.mrd_no.age
            self.gender = self.mrd_no.gender
            self.mobile = self.mrd_no.phone_number
            self.doctor = self.mrd_no.doc_name
            self.vssc_boolean = self.mrd_no.vssc_boolean

    @api.model
    def create(self, vals):
        """Generate a unique billing number in the format: 000001/24-25"""
        if vals.get('bill_number', 'New') == 'New':
            current_year = datetime.now().year
            next_year = current_year + 1
            year_range = f"{str(current_year)[-2:]}-{str(next_year)[-2:]}"

            # Get the next sequence number
            sequence_number = self.env['ir.sequence'].next_by_code('general.billing')

            # Ensure sequence exists
            if not sequence_number:
                sequence_number = '1'
            formatted_seq = str(sequence_number).zfill(4)
            vals['bill_number'] = f"{formatted_seq}/{year_range}"

        return super(GeneralBilling, self).create(vals)

    @api.onchange('department')
    def _onchange_department(self):
        if self.department:
            return {'domain': {'particulars': [('department', '=', self.department.id)]}}
        else:
            return {'domain': {'particulars': []}}

    @api.onchange('particulars')
    def _onchange_particulars(self):
        if self.particulars:
            rate = self.particulars.amount if self.particulars.amount else 0.0
            tax_amount = self.particulars.tax.tax if self.particulars.tax else 0.0
            tax_type = self.particulars.tax_type


            if tax_type == 'inclusive':
                total = rate
            else:
                total = rate + (rate * tax_amount / 100)

            self.general_bill_line_ids = [(0, 0, {
                'particulars': self.particulars.id,
                'rate': rate,
                'tax': self.particulars.tax.id,
                'quantity': 1,
                'total_amt': total,
            })]

    def action_print_general_bill(self):
        return self.env.ref('homeo_doctor.report_general_bill_report').report_action(self)

class BillTYpe(models.Model):
    _name ='bill.type'
    _rec_name = 'bill_type'


    bill_type = fields.Char(string='Bill Type')


class GeneralBillLine(models.Model):
    _name = 'general.bill.line'

    bill_line_id=fields.Many2one('general.billing')
    particulars = fields.Many2one('general.dept.costing',string='Select particulars')
    rate = fields.Integer(string='Rate')
    tax = fields.Many2one('dept.tax', string='Tax(%)')
    quantity = fields.Integer(string='Qty')
    total_amt=fields.Integer(string='Amount',compute="_compute_total", store=True)

    @api.depends('rate', 'tax', 'quantity')
    def _compute_total(self):
        for line in self:
            tax_amount = line.tax.tax if line.tax else 0.0
            line.total_amt = line.rate * line.quantity * (1 + tax_amount / 100)

    @api.onchange('particulars')
    def _rate_auto_fill(self):
        for rec in self:
            rec.rate= rec.particulars.amount




class IPPartBilling(models.Model):
    _name = 'ip.part.billing'
    _description = 'IP Part Billing'
    _rec_name = 'mrd_no'

    bill_number = fields.Char(string='Bill Number',  copy=False, default='New')
    mrd_no = fields.Many2one('patient.reg', string='UHID')
    patient_name = fields.Char(string='Patient Name')
    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    mobile = fields.Char(string='Mobile')
    bill_date = fields.Datetime(string='Bill Date',default=lambda self: datetime.today())
    op_category = fields.Many2one('op.category', string='OP Category')
    doctor = fields.Many2one('doctor.profile', string='Doctor')
    department = fields.Many2one('general.department', string='Department')
    particulars = fields.Many2one('general.dept.costing', string='Select Particulars')
    bill_type = fields.Many2one('bill.type', string='Bill Type')

    ip_no = fields.Char(string='IP No')
    general_bill_line_ids = fields.One2many('ip.part.bill.line','bill_line_id')
    total_item=fields.Char(string='Total Item',compute="_compute_totals")
    total_qty=fields.Char(string='Total Qty',compute="_compute_totals")
    total_tax=fields.Char(string='Total Tax')
    total_amount = fields.Integer(string='Total Amount')
    discount_type =fields.Selection([('amount','Amount'),('percentage','Percentage')],default='percentage')
    discount = fields.Integer(string='Discount')
    oc_type=fields.Selection([('amount','Amount'),('percentage','Percentage')],default='amount',string='O.C Type')
    oc=fields.Integer(string='O.C')
    reference=fields.Selection([('no','No'),('yes','YES')],default='no',string='Reference')
    mode_pay=fields.Selection([('cash', 'Cash'),
                                ('credit', 'Credit'),
                                ('card', 'Card'),
                                ('cheque', 'Cheque'),
                                ('upi', 'UPI'),], string='Payment Method',default='cash')
    net_amount=fields.Integer(string='Net Bill Amount')
    bill_by=fields.Char(string='Bill By')
    remarks =fields.Char(string='Remarks')
    staff_pwd=fields.Char(string='Staff Password')
    staff_name=fields.Many2one('hr.employee',string='Staff Name')
    amount_paid = fields.Integer(string="Amount Paid")
    balance = fields.Integer(string="Balance")
    status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ], string="Status", default="unpaid", tracking=True)

    amount_in_words = fields.Char("Total in Words", compute="_compute_amount_in_words")
    discount_amount = fields.Integer(string="Discount amount")
    rent = fields.Integer(string="Rent",Default=0)
    observation = fields.Boolean(string="Observation")
    observation_status = fields.Selection([
                          ('observation', 'Observation'),
                          ('discharge','Discharge')
                          ], string="Status")
    admitted_date = fields.Date('Admitted Date')
    from_date = fields.Datetime('From Date')
    to_date = fields.Datetime('to Date')
    rent_full_day = fields.Float(string="Full Day Rent")
    rent_half_day = fields.Float(string="Half Day Rent")


    def action_observation(self):
        """Method to toggle observation field when Observation button is clicked"""
        self.observation = True
        # If observation is True, set observation_status to 'observation'
        if self.observation:
            self.observation_status = 'observation'

    def action_observation_discharge(self):
        self.observation = False
        if self.observation:
            self.observation_status = 'discharge'

    @api.onchange('discount', 'discount_type', 'total_amount')
    def _onchange_discount(self):
        """Calculate discount amount and net payable amount based on discount"""
        if self.total_amount:
            if self.discount_type == 'percentage' and self.discount:
                self.discount_amount = (self.total_amount * self.discount) / 100
            elif self.discount_type == 'amount' and self.discount:
                self.discount_amount = self.discount
            else:
                self.discount_amount = 0

            # Calculate net amount (payable amount after discount)
            self.net_amount = self.total_amount - self.discount_amount

    # def action_create_admission(self):
    #     admitted_any = False
    #     warnings = []
    #
    #     for rec in self:
    #         if not rec.mrd_no:
    #             continue
    #
    #         patient = rec.mrd_no  # patient.reg record
    #
    #         if patient.status != 'admitted' and not patient.admission_boolean:
    #             patient.admission_boolean = True
    #             patient.status = 'admitted'
    #             admitted_any = True
    #         else:
    #             warnings.append(f"Patient {patient.patient_id or patient.id} is already admitted.")
    #
    #     if warnings:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Warning',
    #                 'message': '\n'.join(warnings),
    #                 'sticky': True,
    #                 'type': 'warning',
    #             }
    #         }
    #
    #     if not admitted_any:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Info',
    #                 'message': 'No valid billing records with UHID found for admission.',
    #                 'sticky': True,
    #                 'type': 'info',
    #             }
    #         }
    #
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Success',
    #             'message': 'Admission created successfully.',
    #             'sticky': False,
    #             'type': 'success',
    #         }
    #     }
    def action_create_admission(self):
        admitted_any = False
        warnings = []

        for rec in self:
            if not rec.mrd_no:

                vals = {
                    'patient_id': rec.patient_name or 'Unknown',
                    'age': rec.age,
                    'gender': rec.gender,
                    'phone_number': rec.mobile,

                }

                patient = self.env['patient.reg'].create(vals)
                rec.mrd_no = patient
            else:
                patient = rec.mrd_no

            if patient.status != 'admitted' and not patient.admission_boolean:
                patient.admission_boolean = True
                patient.status = 'admitted'
                admitted_any = True
            else:
                warnings.append(f"Patient {patient.patient_id or patient.id} is already admitted.")

        if warnings:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': '\n'.join(warnings),
                    'sticky': True,
                    'type': 'warning',
                }
            }

        if not admitted_any:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': 'No valid billing records with UHID found for admission.',
                    'sticky': True,
                    'type': 'info',
                }
            }

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

    @api.onchange('amount_paid')
    def onchange_amount_paid(self):
        for rec in self:
            if (rec.amount_paid < rec.net_amount and rec.amount_paid > 0):
                rec.balance = rec.net_amount - rec.amount_paid
            elif (rec.amount_paid > rec.net_amount and rec.amount_paid > 0):
                rec.balance = rec.amount_paid - rec.net_amount
            else:
                rec.balance = 0

    @api.depends('total_amount')
    def _compute_amount_in_words(self):
        for record in self:
            record.amount_in_words = num2words(record.total_amount, lang='en').title() + " Only"

    def action_pay_button(self):
        if self.staff_name and self.staff_pwd:
            employee = self.staff_name

            if not employee.staff_password_hash:
                raise ValidationError("This staff has no password set.")

            if self.staff_pwd != employee.staff_password_hash:
                raise ValidationError("The password does not match.")
        else:
            raise ValidationError("Please enter both staff name and password.")
        for record in self:
            record.status = 'paid'

        # Return action to print PDF and show notification
        return {
            'type': 'ir.actions.report',
            'report_name': 'homeo_doctor.report_ip_part_billing_document',
            'report_type': 'qweb-pdf',
            'context': {
                'active_ids': self.ids,
                'active_model': 'ip.part.billing',
            },
            'target': 'new',
        }

    @api.depends('general_bill_line_ids.quantity', 'general_bill_line_ids.total_amt', 'general_bill_line_ids.tax',
                 'rent')
    def _compute_totals(self):
        for record in self:
            record.total_item = len(record.general_bill_line_ids)
            record.total_qty = sum(record.general_bill_line_ids.mapped('quantity'))
            record.total_amount = sum(record.general_bill_line_ids.mapped('total_amt')) + record.rent

            record.total_tax = sum(
                line.tax.tax * line.total_amt / 100 for line in record.general_bill_line_ids if line.tax)

            record.net_amount = sum(record.general_bill_line_ids.mapped('total_amt')) + record.rent

    total_rent_amount = fields.Float(string='Total Rent Amount', compute='_compute_rent_amount', store=True)
    @api.onchange('mrd_no')
    def _onchange_mrd_no(self):
        if self.mrd_no:
            self.patient_name = self.mrd_no.patient_id
            self.age = self.mrd_no.age
            self.gender = self.mrd_no.gender
            self.mobile = self.mrd_no.phone_number
            self.doctor = self.mrd_no.doc_name
            self.admitted_date = self.mrd_no.admitted_date
            self.rent_full_day = self.mrd_no.rent_full
            self.rent_half_day = self.mrd_no.rent_half

    @api.depends('from_date', 'to_date', 'rent_full_day', 'rent_half_day')
    def _compute_rent_amount(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                delta = rec.to_date - rec.from_date
                total_days = delta.days
                seconds = delta.seconds

                if seconds == 0:
                    half_day = False
                elif seconds <= 12 * 3600:
                    half_day = True
                else:
                    total_days += 1
                    half_day = False

                rent = total_days * (rec.rent_full_day or 0)
                if half_day:
                    rent += (rec.rent_half_day or 0)

                rec.total_rent_amount = rent
                print( rec.total_rent_amount,' rec.total_rent_amount rec.total_rent_amount rec.total_rent_amount rec.total_rent_amount rec.total_rent_amount')
            else:
                rec.total_rent_amount = 0

    from datetime import datetime, timedelta
    room_rent_total = fields.Float(string='Room Rent Total', compute='_compute_room_rent_total', store=True)

    @api.depends('general_bill_line_ids.quantity', 'general_bill_line_ids.rate', 'general_bill_line_ids.particulars')
    def _compute_room_rent_total(self):
        for rec in self:
            total = 0.0
            for line in rec.general_bill_line_ids:
                if line.particulars and line.particulars.particular_name == 'Room Rent':
                    total += (line.quantity or 0.0) * (line.rate or 0.0)
            rec.room_rent_total = total


    @api.onchange('from_date', 'to_date', 'total_rent_amount')
    def _onchange_dates_update_rent_line(self):
        for rec in self:
            if rec.total_rent_amount > 0 and rec.from_date and rec.to_date:
                rent_lines = rec.general_bill_line_ids.filtered(
                    lambda l: l.particulars.particular_name == 'Room Rent'
                )

                rent_particular = self.env['general.dept.costing'].search(
                    [('particular_name', '=', 'Room Rent')],
                    limit=1
                )
                if not rent_particular:
                    return

                delta = rec.to_date - rec.from_date
                total_days = delta.days

                # Determine if the checkout time (to_date) is before 12 PM
                half_day = rec.to_date.hour < 12

                # Final quantity logic
                qty = total_days + (0.5 if half_day else 1)

                # Remove old rent lines
                lines = [(2, line.id) for line in rent_lines]

                vals = {
                    'particulars': rent_particular.id,
                    'quantity': qty,
                    'rate': rec.rent_full_day,
                }
                lines.append((0, 0, vals))

                print("Assigning One2many commands with qty:", qty, lines)

                rec.general_bill_line_ids = lines
            else:
                rent_lines = rec.general_bill_line_ids.filtered(
                    lambda l: l.particulars.particular_name == 'Room Rent'
                )
                if rent_lines:
                    lines = [(2, line.id) for line in rent_lines]
                    rec.general_bill_line_ids = lines

    @api.model
    def create(self, vals):
        """Generate a unique billing number in the format: 000001/24-25"""
        if vals.get('bill_number', 'New') == 'New':
            current_year = datetime.now().year
            next_year = current_year + 1
            year_range = f"{str(current_year)[-2:]}-{str(next_year)[-2:]}"

            # Get the next sequence number
            sequence_number = self.env['ir.sequence'].next_by_code('ip.part.billing')

            # Ensure sequence exists
            if not sequence_number:
                sequence_number = '1'
            formatted_seq = str(sequence_number).zfill(4)
            vals['bill_number'] = f"{formatted_seq}/{year_range}"

        return super(IPPartBilling, self).create(vals)

    @api.onchange('department')
    def _onchange_department(self):
        if self.department:
            return {'domain': {'particulars': [('department', '=', self.department.id)]}}
        else:
            return {'domain': {'particulars': []}}

    @api.onchange('particulars')
    def _onchange_particulars(self):
        if self.particulars:
            rate = self.particulars.amount if self.particulars.amount else 0.0
            tax_amount = self.particulars.tax.tax if self.particulars.tax else 0.0
            tax_type = self.particulars.tax_type

            if tax_type == 'inclusive':
                total = rate
            else:
                total = rate + (rate * tax_amount / 100)

            self.general_bill_line_ids = [(0, 0, {
                'particulars': self.particulars.id,
                'rate': rate,
                'tax': self.particulars.tax.id,
                'quantity': 1,
                'total_amt': total,
            })]

    def action_ip_print_general_bill(self):
        return self.env.ref('homeo_doctor.action_report_ip_part_billing').report_action(self)

class IPPartBillLine(models.Model):
    _name = 'ip.part.bill.line'

    bill_line_id=fields.Many2one('ip.part.billing')
    particulars = fields.Many2one('general.dept.costing',string='Select particulars')
    rate = fields.Integer(string='Rate')
    tax = fields.Many2one('dept.tax', string='Tax(%)')
    quantity = fields.Float(string='Qty')
    total_amt=fields.Integer(string='Amount',compute="_compute_total", store=True)

    @api.depends('rate', 'tax', 'quantity')
    def _compute_total(self):
        for line in self:
            tax_amount = line.tax.tax if line.tax else 0.0
            line.total_amt = line.rate * line.quantity * (1 + tax_amount / 100)

    @api.onchange('particulars')
    def _rate_auto_fill(self):
        for rec in self:
            rec.rate= rec.particulars.amount