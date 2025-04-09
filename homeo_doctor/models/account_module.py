from datetime import date

from odoo import models, fields,api,_
from odoo.exceptions import ValidationError


# from odoo.odoo.exceptions import ValidationError


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
    po_number=fields.Many2one('purchase.order',string='PO Number', domain="[('state', '=', 'purchase')]",)
    with_po=fields.Boolean()
    without_po=fields.Boolean()
    invoice_date = fields.Date(
        string="Date",
        default=lambda self: date.today()
    )

    @api.model
    def create(self, vals):
        if vals.get('supplier_invoice', '/') == '/':
            # Get the next number (e.g., '0024')
            raw_seq = self.env['ir.sequence'].next_by_code('supplier.invoice') or '0'
            padded_number = raw_seq.zfill(4)

            # Get last two digits of current year
            year_suffix = str(date.today().year)[-2:]

            # Format as 0024/25
            vals['supplier_invoice'] = "%s/%s" % (padded_number, year_suffix)

        return super(AccountMove, self).create(vals)


    @api.onchange('po_number')
    def _onchange_po_number(self):
        """ Fetch purchase order lines and replace the existing invoice lines """
        if self.po_number:
            self.supplier_name = self.po_number.supplier_name.display_name
            self.invoice_line_ids = [(5, 0, 0)]

            invoice_lines = []
            for line in self.po_number.order_line:
                invoice_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.qty_received,
                    'price_unit': line.price_unit,
                    'account_id': line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id,
                    'tax_ids': [(6, 0, line.taxes_id.ids)],
                    'product_uom_id': line.product_uom.id,
                }))

            self.invoice_line_ids = invoice_lines
        else:
            # If PO is removed, clear invoice lines
            self.invoice_line_ids = [(5, 0, 0)]

    def _default_partner(self):
        return self.env['res.partner'].search([], limit=1)

    partner_id = fields.Many2one('res.partner', string="Customer", required=True, default=_default_partner)
    @api.model
    def create(self, vals):
        if vals.get('move_type') == 'out_invoice' and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.move')
        return super(AccountMove, self).create(vals)

    def action_post(self):
        res = super(AccountMove, self).action_post()

        for move in self:
            if move.move_type == 'in_invoice':
                for line in move.invoice_line_ids:
                    total_qty = line.quantity or 0
                    if line.free_qty:
                        total_qty += line.free_qty  

                    self.env['stock.entry'].create({
                        'invoice_id': move.id,
                        'product_id': line.product_id.id,
                        'quantity': total_qty,
                        'manf_date': line.manufacturing_date,
                        'exp_date': line.expiry_date,
                        'batch': line.batch,
                        'uom_id': line.product_uom_id.id,
                        'rate': line.price_unit,
                        'date': move.invoice_date,
                        'state': 'confirmed',
                    })
                    stock_entries = self.env['stock.entry'].search([
                        ('product_id', '=', line.product_id.id),
                        ('state', '=', 'confirmed'),
                        ('quantity', '>', 0),
                    ])
                    line.stock_in_hand = sum(stock_entries.mapped('quantity'))
        return res


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
    stock_in_hand=fields.Char(string='Stock In Hand', compute="_compute_stock_in_hand", store=True)
    product_uom_category_id = fields.Many2one('uom.category', string="Category", required=True)
    supplier_rack=fields.Many2one('supplier.rack')
    reason_for_rejection=fields.Char('Reason For Rejection')

    @api.depends('product_id')
    def _compute_stock_in_hand(self):
        """Fetch the total available quantity from stock.entry for the selected product."""
        for record in self:
            if record.product_id:
                total_quantity = sum(self.env['stock.entry'].search([
                    ('product_id', '=', record.product_id.id)
                ]).mapped('quantity'))  # Summing up all quantities

                record.stock_in_hand = total_quantity
            else:
                record.stock_in_hand = 0.0

    @api.onchange('quantity')
    def _onchange_ord_qty_quantity(self):
        for line in self:
            if line.ord_qty is not None and line.quantity is not None:
                line.to_be_received = line.ord_qty - line.quantity

            if line.ord_qty < line.quantity:
                line.free_qty = line.quantity - line.ord_qty
                line.quantity = line.ord_qty
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

    @api.onchange('quantity')
    def _onchange_quantity_update_stock(self):
        if self.product_id and self.move_type == 'out_invoice':
            stock_entries = self.env['stock.entry'].search([
                ('product_id', '=', self.product_id.id)
            ], order='id asc')

            qty_to_reduce = self.quantity

            for stock in stock_entries:
                if qty_to_reduce <= 0:
                    break

                if stock.quantity >= qty_to_reduce:
                    stock.quantity -= qty_to_reduce
                    qty_to_reduce = 0
                else:
                    qty_to_reduce -= stock.quantity
                    stock.quantity = 0

            if qty_to_reduce > 0:
                raise ValidationError(_("Not enough stock available for %s!") % self.product_id.name)


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



class StockEntry(models.Model):
    _name = 'stock.entry'
    _description = 'Stock Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Optional for chatter

    name = fields.Char(string="Reference", required=True, copy=False, default=lambda self: _('New'))
    invoice_id = fields.Many2one('account.move', string="Invoice", domain=[('type', '=', 'in_invoice'), ('state', '=', 'posted')])
    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Float(string="Stock In Hand", required=True)
    manf_date=fields.Char(string='M.Date')
    exp_date=fields.Char(string='Exp.date')
    rack=fields.Char(string='Rack Position')
    batch=fields.Char(string='Batch Number')
    rate = fields.Float(string="Rate", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    date=fields.Date(string='Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string="Status", default="draft", tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.entry') or 'New'
        return super(StockEntry, self).create(vals)

    # def write(self, vals):
    #     """Ensure stock quantity doesn't go negative and delete if zero."""
    #     for record in self:
    #         new_qty = vals.get('quantity', record.quantity)
    #         if new_qty < 0:
    #             raise ValidationError(_("Stock quantity cannot be negative!"))
    #
    #     res = super(StockEntry, self).write(vals)
    #
    #     # Delete records where quantity = 0
    #     for record in self:
    #         if record.quantity == 0:
    #             record.unlink()
    #
    #     return res
