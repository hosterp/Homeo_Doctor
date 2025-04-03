from odoo import models, fields, api
from datetime import datetime

class GeneralBilling(models.Model):
    _name = 'general.billing'
    _description = 'General Billing'
    _rec_name = 'bill_number'

    bill_number = fields.Char(string='Bill Number',  copy=False, default='New')
    patient_name = fields.Char(string='Patient Name')
    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    mobile = fields.Char(string='Mobile')
    bill_date = fields.Datetime(string='Bill Date')
    op_category = fields.Many2one('op.category', string='OP Category')
    doctor = fields.Many2one('doctor.profile', string='Doctor')
    department = fields.Many2one('general.department', string='Department')
    particulars = fields.Many2one('general.dept.costing', string='Select Particulars')
    bill_type = fields.Many2one('bill.type', string='Bill Type')
    mrd_no = fields.Char(string='MRD No')
    ip_no = fields.Char(string='IP No')
    general_bill_line_ids = fields.One2many('general.bill.line','bill_line_id')


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
    tax = fields.Many2one('dept.tax', string='Tax')
    quantity = fields.Integer(string='Quantity')
    total_amt=fields.Integer(string='Amount',compute="_compute_total", store=True)

    @api.depends('rate', 'tax', 'quantity')
    def _compute_total(self):
        for line in self:
            tax_amount = line.tax.tax if line.tax else 0.0
            line.total_amt = line.rate * line.quantity * (1 + tax_amount / 100)