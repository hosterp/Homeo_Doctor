import dateutil.utils
from odoo import api, fields, models, tools,_
import odoo.addons
# from datetime import datetime, date
# default=date.today()
class PatientRegistration(models.Model):
    _name = 'patient.registration'
    _description = 'Patient Registration'
    _rec_name = 'reference_no'
    _order = 'reference_no desc'

    reference_no = fields.Char(string="Reference")
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date')
    patient_id = fields.Char(required=True, string="Name")
    address = fields.Text(required=True, string="Address")
    age = fields.Integer(required=True, string="Age")
    phone_number = fields.Char(string="Phone No:",size=12)
    symptoms = fields.Text(required=True, string="Sick")
    remark = fields.Text(string="Remark")
    med_ids = fields.One2many("prescription.entry.lines", 'prescription_line_id', string="Prescription Entry Lines")

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'patient.registrartion.group') or _('New')
        res = super(PatientRegistration, self).create(vals)
        return res

    def _compute_formatted_date(self):
        for record in self:
            if record.date:
                formatted_date = record.date.strftime('%d/%m/%Y')
                record.formatted_date = formatted_date
            else:
                record.formatted_date = ''


class PrescriptionEntryLine(models.Model):
    _name = 'prescription.entry.lines'
    _description = 'Prescription Entry Line'

    prescription_line_id = fields.Many2one("patient.registration", string="Prescription Entry")
    product_id = fields.Many2one('product.product', string="Product")
    total_med = fields.Integer("Tot Med")
    per_ped = fields.Integer("Per Med")
    morn = fields.Boolean("Morn")
    noon = fields.Boolean("Noon")
    night = fields.Boolean("Night")