from datetime import date

from odoo import models, fields,api

class AccountMove(models.Model):
    _inherit = 'account.move'

    # partner_id = fields.Many2one('res.partner', string='Customer', required=False)

    custom_reference = fields.Char(string="Custom Reference")
    doctor=fields.Many2one('doctor.profile',string='Doctor')
    uhid=fields.Many2one('patient.reg',string='UHID')
    patient_name=fields.Char(related='uhid.patient_id',string='Patient Name')
    address=fields.Text(related='uhid.address',string='Address')
    mobile=fields.Char(related='uhid.phone_number',string='Mobile No')
    invoice_line_ids=fields.One2many('account.move.line','move_id')

    supplier_name = fields.Char('Supplier Name')
    supplier_invoice = fields.Char('Invoice No')
    supplier_phone = fields.Char('Phone No')
    supplier_email = fields.Char('Email Id')
    supplier_gst = fields.Char('GST No')
    supplier_dl = fields.Char('DL/REG No')
    supplier_bill_date = fields.Date(string='Bill Date', default=lambda self: date.today())

    invoice_date = fields.Date(
        string="Date",
        default=lambda self: date.today()
    )

    def _default_partner(self):
        return self.env['res.partner'].search([], limit=1)

    partner_id = fields.Many2one('res.partner', string="Customer", required=True, default=_default_partner)
    @api.model
    def create(self, vals):
        if vals.get('move_type') == 'out_invoice' and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.move')
        return super(AccountMove, self).create(vals)



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    gst=fields.Integer(string='GST Rate(%)')
    hsn=fields.Char(string='HSN')
    move_id=fields.Many2one('account.move')
    category = fields.Many2one(
        'medicine.category',
        string="Category",
        store=True,
        ondelete="set null"
    )
    manufacturing_company = fields.Char(string='MFC',store=True)
    batch = fields.Char(string='Batch',store=True)
    manufacturing_date = fields.Date(string='M.Date',store=True)
    expiry_date = fields.Date(string='Exp.Date',store=True)
    move_type = fields.Selection(related='move_id.move_type', store=True)
    ord_qty = fields.Integer(string='Ord.QTY',store=True)
    to_be_received = fields.Integer(string='To Be Rec.',store=True)
    free_qty = fields.Integer(string='Free',store=True)
    rejected_qty = fields.Integer(string='Rejected',store=True)
    supplier_mrp = fields.Integer(string='MRP',store=True)
    quantity = fields.Integer(string='Quantity',store=True)
    supplier_packing = fields.Many2one('supplier.packing', string='Packing')
    stock_in_hand=fields.Char(string='Stock In Hand', store=True)
    product_uom_category_id = fields.Many2one('uom.category', string="Category", required=True)
    supplier_rack=fields.Many2one('supplier.rack')
    reason_for_rejection=fields.Char('Reason For Rejection')
    @api.onchange('ord_qty', 'quantity')
    def _onchange_ord_qty_quantity(self):
        for line in self:
            if line.ord_qty is not None and line.quantity is not None:
                line.to_be_received = line.ord_qty - line.quantity
            else:
                line.to_be_received = 0  # Reset if either field is empty

    @api.onchange('ord_qty')
    def _onchange_ord_qty(self):
        for line in self:
            if line.ord_qty is not None and line.quantity is not None:
                line.to_be_received = line.ord_qty - line.quantity
            else:
                line.to_be_received = 0  # Reset if either field is empty

    @api.onchange('quantity')
    def _onchange_quantity(self):
        for line in self:
            if line.ord_qty is not None and line.quantity is not None:
                line.to_be_received = line.ord_qty - line.quantity
            else:
                line.to_be_received = 0  # Reset if either field is empty

class SupplierRack(models.Model):
    _name='supplier.rack'
    _rec_name='rack'
    rack=fields.Char('Rack')

class UoMCategory(models.Model):
    _inherit = 'uom.category'
    _description = 'Product UoM Categories'
    _rec_name='name'

    name = fields.Char('Category', required=True, translate=True)


class MedicineCategory(models.Model):
    _name = 'medicine.category'
    _rec_name = 'medicine_category'

    medicine_category = fields.Char(string='Category', required=True)
    sequence = fields.Char(string='Category Code', readonly=True)

    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('medicine.category') or '/'
        return super(MedicineCategory, self).create(vals)

class SupplierPacking(models.Model):
    _name='supplier.packing'
    _rec_name = 'supplier_packing'

    supplier_packing=fields.Char(string='Packing')




class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    pay_mode=fields.Selection([('cash','Cash'),('upi','UPI'),('card','Card')],default='cash',string='Payment Mode')
    move_id = fields.Many2one('account.move', string='Invoice')

    uhid = fields.Many2one(related='move_id.uhid', string='UHID', store=True, readonly=True)
    patient_name = fields.Char(related='move_id.patient_name', string='Patient Name', store=True, readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(AccountPaymentRegister, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if active_id:
            move = self.env['account.move'].browse(active_id)
            res.update({
                'move_id': move.id,
                'uhid': move.uhid.id,
                'patient_name': move.patient_name,
            })
        return res
