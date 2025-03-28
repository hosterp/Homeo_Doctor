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
    department = fields.Many2one('general.dept.costing', string='Department')
    particulars = fields.Many2one('general.dept.costing', string='Select Particulars')
    bill_type = fields.Many2one('bill.type', string='Bill Type')
    mrd_no = fields.Char(string='MRD No')
    ip_no = fields.Char(string='IP No')

    @api.model
    def create(self, vals):
        """Generate a unique billing number in the format: 195871/24-25"""
        if vals.get('bill_number', 'New') == 'New':
            current_year = datetime.now().year
            next_year = current_year + 1
            year_range = f"{str(current_year)[-2:]}-{str(next_year)[-2:]}"

            # Ensure sequence is generated correctly
            sequence_number = self.env['ir.sequence'].next_by_code('general.billing')
            if not sequence_number:
                sequence_number = '000001'  # Default if sequence is missing

            vals['bill_number'] = f"{sequence_number}/{year_range}"
        return super(GeneralBilling, self).create(vals)


class BillTYpe(models.Model):
    _name ='bill.type'
    _rec_name = 'bill_type'


    bill_type = fields.Char(string='Bill Type')