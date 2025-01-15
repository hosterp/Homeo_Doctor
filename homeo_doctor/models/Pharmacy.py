from odoo import api, fields, models


class PharmacyDescription(models.Model):
    _name = 'pharmacy.description'
    _description = 'Pharmacy Description'
    _order = 'patient_id desc'
    patient_id = fields.Char(string="Patient ID")
    name = fields.Char(string="Patient Name")
    phone_number = fields.Char(string="Phone Number")
    bill_amount=fields.Integer(string='Bill Amount')
    date= fields.Datetime(string="Date")
    prescription_line_ids = fields.One2many('pharmacy.prescription.line', 'pharmacy_id', string="Prescriptions")

class PharmacyPrescriptionLine(models.Model):
    _name = 'pharmacy.prescription.line'
    _description = 'Pharmacy Prescription Line'

    pharmacy_id = fields.Many2one('pharmacy.description', string="Pharmacy")
    admission_id=fields.Many2one('patient.reg',string='Patient Registration')
    product_id = fields.Many2one('product.product', string="Medicine")
    total_med = fields.Integer("Total Medicine")
    per_ped = fields.Integer("Per Medicine")
    morn = fields.Boolean("Morning")
    noon = fields.Boolean("Noon")
    night = fields.Boolean("Night")
    rate = fields.Float(string='Rate', compute='_compute_rate', store=True)

    @api.depends('product_id', 'total_med')
    def _compute_rate(self):
        for record in self:
            if record.product_id and record.total_med:
                record.rate = record.product_id.list_price * record.total_med
            else:
                record.rate = 0.0
