from num2words import num2words

from odoo import models, fields, api
from datetime import datetime

# from odoo.odoo.tools.safe_eval import dateutil

from datetime import datetime

# from odoo.odoo.exceptions import UserError


# from odoo.odoo.exceptions import UserError


# from odoo.odoo.exceptions import UserError


class GeneralBilling(models.Model):
    _name = 'general.billing'
    _description = 'General Billing'
    _rec_name = 'bill_number'

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
    staff_name=fields.Char(string='Staff Name')
    amount_paid = fields.Integer(string="Amount Paid")
    balance = fields.Integer(string="Balance")
    status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ], string="Status", default="unpaid", tracking=True)

    amount_in_words = fields.Char("Total in Words", compute="_compute_amount_in_words")
    discount_amount = fields.Integer(string="Discount amount")

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

    @api.depends('general_bill_line_ids.quantity', 'general_bill_line_ids.total_amt', 'general_bill_line_ids.tax')
    def _compute_totals(self):
        for record in self:
            record.total_item = len(record.general_bill_line_ids)
            record.total_qty = sum(record.general_bill_line_ids.mapped('quantity'))
            record.total_amount = sum(record.general_bill_line_ids.mapped('total_amt'))

            record.total_tax = sum(
                line.tax.tax * line.total_amt / 100 for line in record.general_bill_line_ids if line.tax)

            record.net_amount = sum(record.general_bill_line_ids.mapped('total_amt'))

    @api.onchange('mrd_no')
    def _onchange_mrd_no(self):
        if self.mrd_no:
            self.patient_name = self.mrd_no.patient_id
            self.age = self.mrd_no.age
            self.gender = self.mrd_no.gender
            self.mobile = self.mrd_no.phone_number
            self.doctor = self.mrd_no.doc_name
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
                sequence_number = '000001'

            vals['bill_number'] = f"{sequence_number}/{year_range}"

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