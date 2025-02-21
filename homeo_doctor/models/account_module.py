from odoo import models, fields

class CustomAccountMove(models.Model):
    _inherit = 'account.move'

    custom_reference = fields.Char(string="Custom Reference")
    doctor=fields.Many2one('doctor.profile',string='Doctor')
    uhid=fields.Many2one('patient.reg',string='UHID')
    patient_name=fields.Char(related='uhid.patient_id',string='Patient Name')
    address=fields.Text(related='uhid.address',string='Address')
    mobile=fields.Char(related='uhid.phone_number',string='Mobile No')