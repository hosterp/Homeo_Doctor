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
    supplier_name = fields.Many2one('res.partner',string='Supplier Name')
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
    pay_mode = fields.Selection([
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('credit', 'Credit'),
    ], string='Payment Mode',default='cash')
    global_discount = fields.Float(string='Discount (%)', digits=(16, 2), default=0.0)
    amount_before_discount = fields.Monetary(string='Amount Before Discount',
                                             store=True, readonly=True, compute='_compute_amount')
    discount_amount = fields.Monetary(string='Discount Amount',
                                      store=True, readonly=True, compute='_compute_amount')

    @api.depends('invoice_line_ids', 'global_discount', 'amount_untaxed')
    def _compute_amount(self):
        # First call the original method to calculate base amounts
        super(AccountMove, self)._compute_amount()

        for move in self:
            # Only apply to supplier invoices
            if move.move_type != 'in_invoice':
                move.amount_before_discount = move.amount_total
                move.discount_amount = 0.0
                continue

            # Store the original amount before discount
            amount_before_discount = move.amount_total
            move.amount_before_discount = amount_before_discount

            # Calculate discount amount
            discount_amount = amount_before_discount * (move.global_discount / 100.0)
            move.discount_amount = discount_amount

            # Update total after discount
            move.amount_total = amount_before_discount - discount_amount

            # Update amount_residual to match the discounted total for unpaid/partially paid invoices
            if move.state == 'posted' and move.payment_state in ['not_paid', 'partial']:
                # Calculate the payment ratio if partially paid
                if move.payment_state == 'partial' and move.amount_residual != 0 and amount_before_discount != 0:
                    paid_ratio = 1 - (move.amount_residual / amount_before_discount)
                    # Apply the same payment ratio to the new discounted total
                    move.amount_residual = (amount_before_discount - discount_amount) * (1 - paid_ratio)
                else:
                    # If not paid at all, residual should equal the new total
                    move.amount_residual = amount_before_discount - discount_amount

                # Update amount_residual_signed accordingly
                move.amount_residual_signed = -move.amount_residual if move.is_inbound() else move.amount_residual

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') in ['New', '/']:
            raw_seq = self.env['ir.sequence'].next_by_code('purchase.order') or '0'
            padded_seq = raw_seq.zfill(4)

            today = date.today()
            year_start = today.year % 100
            year_end = (today.year + 1) % 100
            fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

            vals['name'] = f"{padded_seq}/{fiscal_suffix}"
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

    # @api.model
    # def create(self, vals):
    #     if vals.get('move_type') == 'out_invoice' and not vals.get('name'):
    #         vals['name'] = self.env['ir.sequence'].next_by_code('account.move')
    #
    #     return super(AccountMove, self).create(vals)
    @api.model
    def create(self, vals):
        # 1) If this is a vendor bill, override the default name:
        if vals.get('move_type') == 'in_invoice':
            # Force name to False so we can generate our custom sequence
            vals['name'] = False

            # a) fetch next number from our custom sequence code 'in.invoice'
            #    (You must have created a sequence with code = 'in.invoice')
            raw_seq = self.env['ir.sequence'].next_by_code('in.invoice') or '0'
            padded_seq = str(raw_seq).zfill(4)

            # b) compute fiscal-year suffix, e.g. '25-26' if today is in 2025
            today = fields.Date.context_today(self)
            year_start = today.year % 100
            year_end = (today.year + 1) % 100
            fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

            # c) set name = "0001/25-26"
            vals['name'] = f"{padded_seq}/{fiscal_suffix}"

        # 2) Else if it’s a customer invoice, let Odoo’s default run:
        #    (We do nothing here, so `name` remains whatever default or next_by_code('account.move') gives.)
        #    If you wanted to override out_invoice as well, you could add an elif for move_type == 'out_invoice'.

        return super(AccountMove, self).create(vals)
    def action_post(self):
        res = super(AccountMove, self).action_post()

        for move in self:
            # After posting the invoice, recalculate amount_residual based on discount
            if move.move_type == 'in_invoice' and move.global_discount > 0:
                # Apply discount to residual amount
                move.amount_residual = move.amount_total
                move.amount_residual_signed = -move.amount_residual if move.is_inbound() else move.amount_residual

            if move.move_type == 'in_invoice':
                for line in move.invoice_line_ids:
                    total_qty = line.quantity or 0
                    if line.free_qty:
                        total_qty += line.free_qty

                    self.env['stock.entry'].create({
                        'invoice_id': move.id,
                        'product_id': line.product_id.id,
                        'quantity': total_qty,
                        'hsn': line.hsn,
                        'manf_date': line.manufacturing_date,
                        'exp_date': line.expiry_date,
                        'batch': line.batch,
                        'uom_id': line.product_uom_id.id,
                        'rate': line.price_unit,
                        'date': move.invoice_date,
                        'pack': line.pack,
                        'state': 'confirmed',
                    })
                    stock_entries = self.env['stock.entry'].search([
                        ('product_id', '=', line.product_id.id),
                        ('state', '=', 'confirmed'),
                        ('quantity', '>', 0),
                    ])
                    line.stock_in_hand = sum(stock_entries.mapped('quantity'))
        return res

    def write(self, vals):
        result = super(AccountMove, self).write(vals)
        # If global_discount is being updated on an already posted invoice
        if 'global_discount' in vals and any(move.state == 'posted' for move in self):
            for move in self.filtered(lambda m: m.state == 'posted' and m.move_type == 'in_invoice'):
                # Recalculate amount_residual based on updated discount
                discount_amount = move.amount_before_discount * (move.global_discount / 100.0)
                new_total = move.amount_before_discount - discount_amount

                # Update the amount_residual appropriately
                if move.payment_state == 'not_paid':
                    move.amount_residual = new_total
                elif move.payment_state == 'partial':
                    # Calculate the payment ratio
                    paid_amount = move.amount_before_discount - move.amount_residual
                    if move.amount_before_discount != 0:
                        paid_ratio = paid_amount / move.amount_before_discount
                        move.amount_residual = new_total * (1 - paid_ratio)

                # Update amount_residual_signed accordingly
                move.amount_residual_signed = -move.amount_residual if move.is_inbound() else move.amount_residual

        return result


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
    product_uom_category_id = fields.Many2one('uom.category', string="Category")
    supplier_rack=fields.Many2one('supplier.rack')
    reason_for_rejection=fields.Char('Reason For Rejection')
    pack = fields.Integer('Pack',default=1)
    pup = fields.Float('PUP',compute="pup_calculation")

    @api.depends('pack','price_unit')
    def pup_calculation(self):
        for line in self:
            line.pup = line.price_unit/line.pack

    @api.onchange('product_id')
    def _onchange_product_id_hsn(self):
        for line in self:
            if line.product_id and line.product_id.l10n_in_hsn_code:
                line.hsn = line.product_id.l10n_in_hsn_code

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

    pay_mode = fields.Selection([('cash', 'Cash'), ('upi', 'UPI'), ('card', 'Card'), ('credit', 'Credit')],
                                default='cash', string='Payment Mode')
    move_id = fields.Many2one('account.move', string='Invoice')

    uhid = fields.Many2one(related='move_id.uhid', string='UHID', store=True, readonly=True)
    patient_name = fields.Char(related='move_id.patient_name', string='Patient Name', store=True, readonly=True)
    global_discount = fields.Float(related='move_id.global_discount', string='Discount (%)', readonly=True)
    amount_before_discount = fields.Monetary(related='move_id.amount_before_discount', string='Amount Before Discount',
                                             readonly=True)
    discount_amount = fields.Monetary(related='move_id.discount_amount', string='Discount Amount', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super(AccountPaymentRegister, self).default_get(fields_list)
        active_ids = self._context.get('active_ids')

        if active_ids and len(active_ids) == 1:
            move = self.env['account.move'].browse(active_ids[0])
            res.update({
                'move_id': move.id,
                'uhid': move.uhid.id if move.uhid else False,
                'patient_name': move.patient_name,
            })

            # If there's a discount, explicitly set the amount
            if move.global_discount > 0:
                res['amount'] = move.amount_total

                # Also update payment_difference if it's in the fields
                if 'payment_difference' in fields_list:
                    res['payment_difference'] = 0.0

        return res

    def write(self, vals):
        res = super(AccountPaymentRegister, self).write(vals)
        if 'pay_mode' in vals and self.move_id:
            self.move_id.write({'pay_mode': vals['pay_mode']})
        return res

    @api.model
    def create(self, vals):
        record = super(AccountPaymentRegister, self).create(vals)
        if 'pay_mode' in vals and record.move_id:
            record.move_id.write({'pay_mode': vals['pay_mode']})
        return record

    @api.onchange('source_amount', 'source_currency_id', 'company_id', 'currency_id', 'payment_date')
    def _onchange_amount(self):
        if hasattr(super(AccountPaymentRegister, self), '_onchange_amount'):
            super(AccountPaymentRegister, self)._onchange_amount()

        # After any amount calculation, apply discount if necessary
        if self.move_id and self.move_id.global_discount > 0:
            self.amount = self.move_id.amount_total

    @api.onchange('journal_id')
    def _onchange_journal(self):
        # After journal change, reapply discount if necessary
        if self.move_id and self.move_id.global_discount > 0:
            self.amount = self.move_id.amount_total

    # Override the _create_payment_vals_from_wizard method to use the correct amount
    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()

        # Check if payment_vals is a dictionary (single payment)
        if isinstance(payment_vals, dict):
            # If we're paying an invoice with a discount, make sure we use the discounted amount
            if self.move_id and self.move_id.global_discount > 0:
                payment_vals['amount'] = self.move_id.amount_total

        # Check if payment_vals is a list of dictionaries (batch payments)
        elif isinstance(payment_vals, list) and all(isinstance(item, dict) for item in payment_vals):
            # If we're paying an invoice with a discount, make sure we use the discounted amount
            if self.move_id and self.move_id.global_discount > 0:
                for val in payment_vals:
                    if 'amount' in val:
                        val['amount'] = self.move_id.amount_total

        return payment_vals

    # This method is called when the form is initialized
    def _compute_payment_amount(self):
        for wizard in self:
            # Call the original method
            super(AccountPaymentRegister, wizard)._compute_payment_amount()

            # Then override the amount if there's a discount
            if wizard.move_id and wizard.move_id.global_discount > 0:
                wizard.amount = wizard.move_id.amount_total

class StockEntry(models.Model):
    _name = 'stock.entry'
    _description = 'Stock Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Optional for chatter

    name = fields.Char(string="Reference", required=True, copy=False, default=lambda self: _('New'))
    invoice_id = fields.Many2one('account.move', string="Invoice", domain=[('type', '=', 'in_invoice'), ('state', '=', 'posted')])
    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Float(string="Stock In Hand", required=True)
    manf_date=fields.Char(string='M.Date')
    hsn=fields.Char(string='HSN')
    exp_date=fields.Char(string='Exp.date')
    rack=fields.Char(string='Rack Position')
    batch=fields.Char(string='Batch Number')
    rate = fields.Float(string="Rate", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    date=fields.Date(string='Date')
    pack = fields.Integer(string="Pack",default=1)
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
