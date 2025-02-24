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

    def _default_partner(self):
        return self.env['res.partner'].search([], limit=1)

    partner_id = fields.Many2one('res.partner', string="Customer", required=True, default=_default_partner)
    @api.model
    def create(self, vals):
        if vals.get('move_type') == 'out_invoice' and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.move')
        return super(AccountMove, self).create(vals)

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
    manufacturing_company = fields.Char('MFC')
    hsn_code = fields.Char('HSN')
    batch = fields.Char('Batch')
    manufacturing_date = fields.Date('M.Date')
    expiry_date = fields.Date('Exp.Date')
    move_type = fields.Selection(related='move_id.move_type', store=True)




class MedicineCategory(models.Model):
    _name = 'medicine.category'
    _rec_name = 'medicine_category'

    medicine_category = fields.Char(string='Category', required=True)
    sequence = fields.Char(string='Category Code', readonly=True)

    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('medicine.category') or '/'
        return super(MedicineCategory, self).create(vals)
