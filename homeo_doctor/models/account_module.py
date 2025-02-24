from odoo import models, fields

class CustomAccountMove(models.Model):
    _inherit = 'account.move'

    custom_reference = fields.Char(string="Custom Reference")
    doctor=fields.Many2one('doctor.profile',string='Doctor')
    uhid=fields.Many2one('patient.reg',string='UHID')
    patient_name=fields.Char(related='uhid.patient_id',string='Patient Name')
    address=fields.Text(related='uhid.address',string='Address')
    mobile=fields.Char(related='uhid.phone_number',string='Mobile No')
    invoice_line_ids=fields.One2many('account.move.line','move_id')



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    gst=fields.Integer(string='GST Rate(%)')
    move_id=fields.Many2one('account.move')
    category = fields.Many2one(
        'medicine.category',
        string="Category",
        store=True,
        ondelete="set null"
    )




class MedicineCategory(models.Model):
    _name = 'medicine.category'
    _rec_name = 'medicine_category'


    medicine_category=fields.Char(string='Category')