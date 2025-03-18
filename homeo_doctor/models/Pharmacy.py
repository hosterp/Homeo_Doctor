from odoo import api, fields, models


class PharmacyDescription(models.Model):
    _name = 'pharmacy.description'
    _description = 'Pharmacy Description'
    _order = 'patient_id desc'
    patient_id = fields.Many2one('patient.registration',string="Patient ID")
    name = fields.Char(string="Patient Name")
    phone_number = fields.Char(string="Phone Number")
    # bill_amount=fields.Integer(string='Bill Amount')
    doctor_name=fields.Char(string='Doctor')
    date= fields.Datetime(string="Date",default=fields.Datetime.now)
    prescription_line_ids = fields.One2many('pharmacy.prescription.line', 'pharmacy_id', string="Prescriptions")
    bill_amount = fields.Float(string="Total Bill Amount", compute="_compute_bill_amount", store=True)

    @api.depends('prescription_line_ids.rate', 'prescription_line_ids.gst')
    def _compute_bill_amount(self):
        for rec in self:
            rec.bill_amount = sum(line.rate for line in rec.prescription_line_ids)  # Excluding GST

class PharmacyPrescriptionLine(models.Model):
    _name = 'pharmacy.prescription.line'
    _description = 'Pharmacy Prescription Line'

    pharmacy_id = fields.Many2one('pharmacy.description', string="Pharmacy")
    admission_id=fields.Many2one('patient.reg',string='Patient Registration')
    product_id = fields.Many2one('product.product', string="Medicine")
    total_med = fields.Integer("Total Medicine")
    per_ped = fields.Integer("Per Medicine")
    morn = fields.Integer("Morning")
    noon = fields.Integer("Noon")
    night = fields.Integer("Night")
    category=fields.Char(string='Category')
    hsn=fields.Char(string='HSN')
    batch=fields.Char(string='Batch')
    manf_date=fields.Date(string='M.Date')
    exp_date=fields.Date(string='Exp.Date')
    packing=fields.Char(string='Packing')
    mfc=fields.Char(string='MFC')
    qty=fields.Integer(string='QTY')
    gst=fields.Integer(string='GST Rate(%)')
    discount=fields.Float(string='Disc %')
    stock_in_hand = fields.Char(string='Stock In Hand', compute="_compute_stock_in_hand", store=True)
    rate = fields.Float(string='Rate', store=True)

    @api.depends('product_id')
    def _compute_stock_in_hand(self):
        """Fetch the total available quantity from stock.entry for the selected product."""
        for record in self:
            if record.product_id:
                total_quantity = sum(self.env['stock.entry'].search([
                    ('product_id', '=', record.product_id.id)
                ]).mapped('quantity'))  # Summing up all quantities

                record.stock_in_hand = total_quantity
                record.per_ped = record.product_id.lst_price

            else:
                record.stock_in_hand = 0.0

    @api.onchange('qty')
    def _onchange_qty(self):
        for rec in self:
            if rec.qty:
                rec.rate = rec.per_ped * rec.qty
    # @api.depends('product_id', 'total_med')
    # def _compute_rate(self):
    #     for record in self:
    #         if record.product_id and record.total_med:
    #             record.rate = record.product_id.list_price * record.total_med
    #         else:
    #             record.rate = 0.0
