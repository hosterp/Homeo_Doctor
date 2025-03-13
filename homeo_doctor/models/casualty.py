import re
from datetime import date
from odoo.exceptions import UserError

import dateutil.utils
from odoo import api, fields, models, tools,_




class PatientRegistration(models.Model):
    _name = 'casualty.reg'
    _description = 'Casualty Registration'
    _rec_name = 'casualty_no'
    _order = 'casualty_no desc'

    casualty_no = fields.Char(string="UHID")
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    patient_id = fields.Char( string="Name")
    address = fields.Text( string="Address")
    age = fields.Char(string="Age" , store=True)
    phone_number = fields.Char(string="Mobile No" ,size=12)
    email = fields.Char(string="Email ID")
    pin_code = fields.Char(string="PIN Code")
    id_proof = fields.Binary(string='Upload VSSC ID Proof')
    vssc_id = fields.Char(string="VSSC ID No")
    vssc_boolean = fields.Boolean(string='VSSC', default=False)
    # department_id =fields.Char(string='Department')
    doc_name =fields.Char(string='Doctor')
    registration_fee = fields.Float(string="Registration Fee", default=50.0)
    remark = fields.Text(string="Remark")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    prescription_line_ids=fields.One2many('prescription.casualty.entry.lines','prescription_line_id')
    prescription_boolean=fields.Boolean(default=False)
    no_consultation = fields.Boolean(default= False)
    @api.model
    def create(self, vals):
        if not vals.get('casualty_no'):
            vals['casualty_no'] = self.env['ir.sequence'].next_by_code('casualty.reg') or '/'
        return super(PatientRegistration, self).create(vals)

    def action_admit_patient(self):
        # Prepare the data to pass
        patient_data = {
            'patient_id': self.patient_id,
            'address': self.address,
            'age': self.age,
            'phone_number': self.phone_number,
            'email': self.email,
            'pin_code': self.pin_code,
            'id_proof': self.id_proof,
            'vssc_id': self.vssc_id,
            'vssc_boolean': self.vssc_boolean,
            'admission_boolean':True,
            'no_consultation':False,
        }

        # Create a new record in the target model with the patient data
        # Replace 'patient.admission' with your actual target model
        admission_record = self.env['patient.reg'].create(patient_data)

    def action_fill_prescription(self):
        self.prescription_boolean=True
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Prescription Entry',
        #     'res_model': 'prescription.casualty.entry.lines',
        #     'view_mode': 'tree,form',
        #     'target': 'current',
        #     'domain': [('prescription_line_id', '=', self.id)],
        #     'context': {'default_prescription_line_id': self.id},
        # }


class PrescriptionCasualtyEntryLine(models.Model):
    _name = 'prescription.casualty.entry.lines'
    _description = 'Prescription Casualty Entry Line'

    prescription_line_id = fields.Many2one("casualty.reg", string="Prescription Entry")
    product_id = fields.Many2one('product.product', string="Medicine")
    # total_med = fields.Integer("Tot Med")
    # per_ped = fields.Integer("Per Med")
    morn = fields.Integer("Morn")
    noon = fields.Integer("Noon")
    night = fields.Integer("Night")