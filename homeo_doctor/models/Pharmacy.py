import logging
from collections import defaultdict
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError, _logger
import math
class PharmacyDescription(models.Model):
    _name = 'pharmacy.description'
    _description = 'Pharmacy Description'
    _order = 'date desc'
    _rec_name='bill_number'


    patient_id = fields.Many2one('patient.registration',string="UHID")
    uhid_id = fields.Many2one('patient.reg', string="UHID", ondelete='set null')
    name = fields.Char(string="Patient Name")
    phone_number = fields.Char(string="Phone Number")
    # bill_amount=fields.Integer(string='Bill Amount')
    doctor_name=fields.Many2one('doctor.profile',string='Doctor')
    date= fields.Datetime(string="Date",default=fields.Datetime.now)
    prescription_line_ids = fields.One2many('pharmacy.prescription.line', 'pharmacy_id', string="Prescriptions")
    bill_amount = fields.Float(string="Total Bill Amount", compute="_compute_bill_amount", store=True)
    partner_id = fields.Many2one('res.partner', string="Related Partner")
    total_item=fields.Integer(string='Total Item', compute="_compute_totals")
    total_qty=fields.Integer(string='Total Qty', compute="_compute_totals")
    total_amount=fields.Integer(string='Total Amount', compute="_compute_totals")
    payment_mathod=fields.Selection([('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'),('credit','Credit')],string='Payment Method',default='cash')
    paid_amount = fields.Integer(string='Paid Amount')
    balance = fields.Integer(string='Balance Amount')
    status=fields.Selection([('unpaid','Unpaid'),('paid','Paid'),('cancelled', 'Cancelled')],default='unpaid',string='Payment Status')
    status_admitted=fields.Selection([('admitted','Admitted')],string='Status')
    bill_by = fields.Char(string='Bill By')
    remarks = fields.Char(string='Remarks')
    staff_pwd = fields.Char(string='Staff Password')
    staff_name = fields.Many2one('hr.employee',string='Staff Name')
    description_line_ids = fields.One2many('pharmacy.prescription.line', 'description_id', string="Lines")
    bill_number = fields.Char(string="Bill Number", readonly=True, copy=False, default='New')
    admitted_boolean=fields.Boolean('Admitted')
    patient_type=fields.Selection([('insurance','Insurance Patient'),('normal','Normal Patient')])
    # @api.model
    # def create(self, vals):
    #     if vals.get('bill_number', 'New') == 'New':
    #         seq = self.env['ir.sequence'].next_by_code('pharmacy.description')
    #         print(f"Generated sequence: {seq}")
    #         vals['bill_number'] = seq or 'New'
    #     return super(PharmacyDescription, self).create(vals)

    active = fields.Boolean(default=True)
    op_category=fields.Selection([('op','OP'),('ip','IP'),('others','OTHERS')])
    vssc_boolean=fields.Boolean(string='VSSC')
    @api.onchange('patient_type')
    def  _onchange_patient_type(self):
        for rec in self:
            if rec.patient_type == 'insurance':
                rec.payment_mathod ='credit'

    def action_cancel(self):
        for record in self:
            record.status = 'cancelled'

    def get_cancelled_bills(self):
        return self.search([('active', '=', False)])

    def get_modified_bills(self):
        return self.search([('write_date', '!=', False), ('write_date', '!=', 'create_date')])

    def get_active_bills(self):
        return self.search([('active', '=', True)])

    def unlink(self):
        for rec in self:
            rec.active = False
        return True

    @api.onchange('uhid_id')
    def _onchange_uhid_id(self):
        if self.uhid_id:
            self.name = self.uhid_id.patient_id
            self.phone_number = self.uhid_id.phone_number
            self.vssc_boolean = self.uhid_id.vssc_boolean
            # self.patient_age = self.uhid_id.age
            # self.patient_gender = self.uhid_id.gender

    @api.onchange('paid_amount')
    def _onchange_paymode(self):
        for rec in self:
            if rec.total_amount and rec.paid_amount:
                rec.balance = abs(rec.total_amount - rec.paid_amount)

    @api.depends('prescription_line_ids')
    def _compute_totals(self):
        for rec in self:
            rec.total_item = len(rec.prescription_line_ids)
            rec.total_qty = sum(line.qty for line in rec.prescription_line_ids)
            rec.total_amount = sum(line.rate for line in rec.prescription_line_ids)

    @api.model
    def create(self, vals):
        if vals.get('bill_number', 'New') == 'New':
            seq_number = self.env['ir.sequence'].next_by_code('pharmacy.description') or '0000'
            today = date.today()
            year_start = today.year % 100
            year_end = (today.year + 1) % 100
            fiscal_suffix = f"{year_start:02d}-{year_end:02d}"

            vals['bill_number'] = f"{seq_number}/{fiscal_suffix}"
        res = super(PharmacyDescription, self).create(vals)
        res._process_payment()

        # # Ensure partner creation is only done if necessary
        # if not res.partner_id and res.name:
        #     partner = self.env['res.partner'].search([
        #         ('name', '=', res.name),
        #         # Add other fields to match if needed
        #     ], limit=1)
        #
        #     if not partner:
        #         partner = self.env['res.partner'].create({
        #             'name': res.name,
        #             # Add other values as needed
        #         })
        #
        #     res.partner_id = partner.id
        #
        return res

    def write(self, vals):
        res = super(PharmacyDescription, self).write(vals)
        for record in self:
            record._process_payment()
        return res
    @api.depends('prescription_line_ids.rate', 'prescription_line_ids.gst')
    def _compute_bill_amount(self):
        for rec in self:
            rec.bill_amount = sum(line.rate for line in rec.prescription_line_ids)  # Excluding GST

    def _process_payment(self):
        # Check if the context already has the 'payment_processed' flag
        if self.env.context.get('payment_processed', False):
            return  # Skip processing if payment already processed

        # Add the flag to the context
        context = dict(self.env.context, payment_processed=True)
        self = self.with_context(context)

        if self.payment_mathod == 'credit':
            for line in self.prescription_line_ids:
                if line.product_id and line.qty:
                    stock_entries = self.env['stock.entry'].search([
                        ('product_id', '=', line.product_id.id)
                    ], order="id asc")

                    remaining_qty = line.qty
                    for entry in stock_entries:
                        if remaining_qty <= 0:
                            break
                        if entry.quantity >= remaining_qty:
                            entry.quantity -= remaining_qty
                            remaining_qty = 0
                        else:
                            remaining_qty -= entry.quantity
                            entry.quantity = 0

                    line.stock_in_hand = sum(stock_entries.mapped('quantity'))

    def action_register_payment(self):
        if self.staff_name and self.staff_pwd:
            employee = self.staff_name

            if not employee.staff_password_hash:
                raise ValidationError("This staff has no password set.")

            if self.staff_pwd != employee.staff_password_hash:
                raise ValidationError("The password does not match.")
        else:
            raise ValidationError("Please enter both staff name and password.")
        for record in self:
            for line in record.prescription_line_ids:
                if line.product_id and line.qty:

                    stock_entries = self.env['stock.entry'].search([
                        ('product_id', '=', line.product_id.id)
                    ], order="id asc")

                    remaining_qty = line.qty
                    for entry in stock_entries:
                        if remaining_qty <= 0:
                            break
                        if entry.quantity >= remaining_qty:
                            entry.quantity -= remaining_qty
                            remaining_qty = 0
                        else:
                            remaining_qty -= entry.quantity
                            entry.quantity = 0
                    line.stock_in_hand = sum(stock_entries.mapped('quantity'))
            record.status = 'paid'

        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': 'Payment Confirmed',
        #         'message': f'Payment has been confirmed for {self.name}',
        #         'sticky': False,
        #         'next': {'type': 'ir.actions.act_window_close'},
        #     }
        # }

        return self.env.ref('homeo_doctor.action_pharmacy_report').report_action(self)
        # partner = False
        # if self.patient_id and hasattr(self.patient_id, 'partner_id') and self.patient_id.partner_id:
        #     partner = self.patient_id.partner_id.id
        # else:
        #     # Look for existing partner with same name/phone
        #     partner = self.env['res.partner'].search([
        #         ('name', '=', self.name),
        #         ('phone', '=', self.phone_number)
        #     ], limit=1)
        #
        #     if not partner:
        #         # Create a new partner for this patient
        #         partner = self.env['res.partner'].create({
        #             'name': self.name,
        #             'phone': self.phone_number,
        #         }).id
        #     else:
        #         partner = partner.id
        #
        # return {
        # 'name': 'Register Payment',
        # 'type': 'ir.actions.act_window',
        # 'res_model': 'account.payment',
        # 'view_mode': 'form',
        # 'view_id': self.env.ref('homeo_doctor.view_account_payment_form_inherit').id,
        # 'target': 'new',
        # 'context': {
        #     'default_pharm_id': self.id,
        #     'default_amount': self.bill_amount,
        #     'default_payment_type': 'inbound',
        #     'default_communication': self.name,  # This is fine, communication isn't used for sequence
        #     'default_payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
        #     'default_journal_id': self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id,
        #     # Remove the next line to let Odoo handle the sequence
        #     'default_name': self.name,
        #     'default_uhid': self.patient_id.id if self.patient_id else False,
        #     'default_partner_id': partner,
        #     'default_partner_type': 'customer',
        # }
    # }

    def view_prescription_details(self):
        """
        Open a view of prescription details for this pharmacy record
        """
        self.ensure_one()
        return {
            'name': 'Prescription Details',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'pharmacy.prescription.line',
            'domain': [('pharmacy_id', '=', self.id)],
            'target': 'new',
            'context': self.env.context,
        }

    def amount_to_text_indian(self):
        """Convert amount to words in Indian format (Rupees and Paise)."""
        try:
            from num2words import num2words
            if self.total_amount:
                amount_int = int(self.total_amount)
                decimal_part = int(round((self.total_amount - amount_int) * 100))

                rupees_text = num2words(amount_int, lang='en_IN').title()
                result = f" {rupees_text}"

                if decimal_part:
                    paise_text = num2words(decimal_part, lang='en_IN').title()
                    result += f" and {paise_text} Paise"

                return result + " Only"
        except Exception as e:
            # Optional: log the error for debugging
            _logger = logging.getLogger(__name__)
            _logger.warning("Failed to convert amount to Indian text: %s", e)

            # Fallback
            return self.currency_id.amount_to_text(self.total_amount)

        return ""


class PharmacyPrescriptionLine(models.Model):
    _name = 'pharmacy.prescription.line'
    _description = 'Pharmacy Prescription Line'

    pharmacy_id = fields.Many2one('pharmacy.description', string="Pharmacy")
    admission_id=fields.Many2one('patient.reg',string='Patient Registration')
    product_id = fields.Many2one('product.product', string="Medicine")
    total_med = fields.Integer("Total Medicine")
    per_ped = fields.Float("Per Medicine")
    morn = fields.Integer("Morning")
    noon = fields.Integer("Noon")
    night = fields.Integer("Night")
    category=fields.Char(string='Category')
    batch = fields.Char(string="Batch", compute="_compute_product_details", store=True)
    manf_date = fields.Date(string="Manufacturing Date", compute="_compute_product_details", store=True)
    exp_date = fields.Date(string="Expiry Date", compute="_compute_product_details", store=True)
    rate = fields.Float(string="Rate", store=True)
    supplier_rate = fields.Float(string="Rate")
    hsn = fields.Char(string="HSN Code", compute="_compute_product_details", store=True)
    packing=fields.Char(string='Packing')
    mfc=fields.Char(string='Manufacturer')
    qty=fields.Integer(string='QTY')
    gst=fields.Integer(string='GST Rate(%)')
    discount=fields.Float(string='Disc %')
    stock_in_hand = fields.Char(string='Stock In Hand', compute="_compute_stock_in_hand", store=True)
    # rate = fields.Float(string='Rate', store=True)
    description_id = fields.Many2one('pharmacy.description', string="Sale Reference")


    @api.depends('rate', 'gst')
    def _compute_tax_components(self):
        for rec in self:
            if rec.gst:
                base = rec.rate / (1 + rec.gst / 100.0)
                rec.taxable = base
                rec.cgst = base * (rec.gst / 200.0)
                rec.sgst = base * (rec.gst / 200.0)
            else:
                rec.taxable = rec.rate
                rec.cgst = 0.0
                rec.sgst = 0.0

    taxable = fields.Float("Taxable Amount", compute="_compute_tax_components", store=True)
    cgst = fields.Float("CGST", compute="_compute_tax_components", store=True)
    sgst = fields.Float("SGST", compute="_compute_tax_components", store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                stock_entry = self.env['stock.entry'].search([
                    ('product_id', '=', line.product_id.id),
                    ('quantity', '>', 0),
                    # ('state', '=', 'confirmed'),
                    # ('exp_date', '>', fields.Date.today()),
                ], order='exp_date asc', limit=1)

                if stock_entry:
                    line.batch = stock_entry.batch
                    line.manf_date = stock_entry.manf_date
                    line.exp_date = stock_entry.exp_date
                    line.per_ped = stock_entry.pup
                    line.supplier_rate = stock_entry.rate
                    line.hsn = stock_entry.hsn
                    line.mfc = stock_entry.company
                    line.gst = stock_entry.gst
                    # line.uom_id = stock_entry.uom_id.id

    @api.depends('product_id')
    def _compute_product_details(self):
        for line in self:
            if line.product_id:
                stock_entry = self.env['stock.entry'].search([
                    ('product_id', '=', line.product_id.id),
                    ('quantity', '>', 0),
                    # ('exp_date', '>', fields.Date.today()),
                ], order='exp_date asc', limit=1)

                if stock_entry:
                    line.batch = stock_entry.batch
                    line.manf_date = stock_entry.manf_date
                    line.exp_date = stock_entry.exp_date
                    # line.rate = stock_entry.rate
                    line.hsn = stock_entry.hsn
                # else:

                    # line.batch = False
                    # line.manf_date = False
                    # line.exp_date = False
                    # line.rate = 0.0
                    # line.hsn = False
    @api.depends('product_id')
    def _compute_stock_in_hand(self):
        """Fetch the total available quantity from stock.entry for the selected product."""
        for record in self:
            if record.product_id:
                total_quantity = sum(self.env['stock.entry'].search([
                    ('product_id', '=', record.product_id.id)
                ]).mapped('quantity'))  # Summing up all quantities

                record.stock_in_hand = total_quantity
                # record.per_ped = record.product_id.lst_price
                # record.supplier_rate = record.product_id.standard_price


            else:
                record.stock_in_hand = 0.0

    @api.model
    def create(self, vals):
        """Deduct the quantity from stock when a record is created."""
        record = super(PharmacyPrescriptionLine, self).create(vals)
        if record.product_id and record.qty:
            stock_entries = self.env['stock.entry'].search([
                ('product_id', '=', record.product_id.id)
            ], order="id asc")

            remaining_qty = record.qty
            for entry in stock_entries:
                if remaining_qty <= 0:
                    break
                if self.stock_in_hand >= remaining_qty:
                    self.stock_in_hand -= remaining_qty
                    remaining_qty = 0
                else:
                    remaining_qty -= self.stock_in_hand
                    self.stock_in_hand = 0

        return record

    def write(self, vals):
        """Adjust stock when updating records."""
        for record in self:
            original_qty = record.qty
            new_qty = vals.get('quantity', original_qty)

            if original_qty != new_qty:
                diff = new_qty - original_qty  # If increased, need to deduct more

                stock_entries = self.env['stock.entry'].search([
                    ('product_id', '=', record.product_id.id)
                ], order="id asc")

                remaining_qty = diff
                for entry in stock_entries:
                    if remaining_qty <= 0:
                        break
                    if entry.quantity >= remaining_qty:
                        entry.quantity -= remaining_qty
                        remaining_qty = 0
                    else:
                        remaining_qty -= entry.quantity
                        entry.quantity = 0

        return super(PharmacyPrescriptionLine, self).write(vals)

    @api.onchange('qty')
    def _onchange_qty(self):
        for rec in self:
            if rec.qty:
                product = rec.per_ped * rec.qty
                rec.rate = math.ceil(product)
    # @api.depends('product_id', 'total_med')
    # def _compute_rate(self):
    #     for record in self:
    #         if record.product_id and record.total_med:
    #             record.rate = record.product_id.list_price * record.total_med
    #         else:
    #             record.rate = 0.0



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], default='draft')
    pharm_id = fields.Many2one('pharmacy.description', string="Pharmacy Record")
    name = fields.Char(string="Patient Name")  # Make this a regular field, not related
    uhid = fields.Many2one('patient.registration', string="UHID")  # Make this a regular field, not related
    pay_mode = fields.Selection([('cash','Cash'),('upi','UPI'),('card','Card')])
    paid_mount = fields.Integer(string='Paid Amount')
    balance = fields.Integer(string='Balance Amount')

    @api.onchange('pharm_id')
    def _onchange_pharm_id(self):
        if self.pharm_id:
            self.name = self.pharm_id.name  # Changed from patient_name to name
            self.uhid = self.pharm_id.patient_id.id if self.pharm_id.patient_id else False
            # Set the partner_id from the patient if it exists
            if self.pharm_id.patient_id and hasattr(self.pharm_id.patient_id, 'partner_id'):
                self.partner_id = self.pharm_id.patient_id.partner_id.id
            # If patient has no partner_id, create a partner or find existing one
            elif self.pharm_id.patient_id:
                # Look for existing partner with the same name/phone
                partner = self.env['res.partner'].search([
                    ('name', '=', self.pharm_id.name),
                    ('phone', '=', self.pharm_id.phone_number)
                ], limit=1)

                if not partner:
                    # Create a new partner
                    partner = self.env['res.partner'].create({
                        'name': self.pharm_id.name,
                        'phone': self.pharm_id.phone_number,
                    })

                self.partner_id = partner.id

    # Override the action_post method to ensure partner_id is set
    def action_post(self):


        # If this payment is linked to a pharmacy record, generate PDF
        if self.pharm_id:
            # Create report action context
            context = dict(self.env.context)

            # Get the pharmacy report action
            report_action = self.env.ref('homeo_doctor.action_pharmacy_report')

            # Return the report action with the pharmacy record
            return report_action.with_context(active_model='pharmacy.description',
                                            active_ids=[self.pharm_id.id]).report_action(self.pharm_id)

        return

    @api.onchange('paid_mount', 'balance')
    def _onchange_paymode(self):
        for rec in self:
            if rec.amount > 0:
                if rec.paid_mount > 0:
                    rec.balance = rec.amount - rec.paid_mount
                    # Ensure amount remains consistent
                    if rec.balance < 0:
                        rec.balance = 0

    @api.depends('paid_mount')
    def _compute_balance(self):
        for rec in self:
            rec.balance = max(0, rec.amount - rec.paid_mount)



class PharmacyReturn(models.Model):
    _name = 'pharmacy.return'
    _description = 'Pharmacy Sales Return'
    _order = 'return_date desc'
    _rec_name='return_number'

    return_date = fields.Datetime(string="Return Date",default=fields.Datetime.now)
    original_sale_id = fields.Many2one('pharmacy.description', string="Original Bill")
    return_line_ids = fields.One2many('pharmacy.return.line', 'return_id', string="Return Lines")
    total_return_amount = fields.Float(string="Total Return Amount", compute="_compute_return_amount", store=True)
    patient_id = fields.Many2one(related='original_sale_id.uhid_id', string="UHID", store=True, readonly=True)
    patient_name = fields.Char(related='original_sale_id.name', string="Patient Name", store=True, readonly=True)
    phone_number = fields.Char(related='original_sale_id.phone_number', string="Phone Number", store=True,
                               readonly=True)
    doctor_name = fields.Many2one(related='original_sale_id.doctor_name', string="Doctor", store=True, readonly=True)
    return_number = fields.Char(
        string="Return No",
        readonly=True,
        copy=False,
        default='/',
    )

    def print_original_bill(self):
        self.ensure_one()
        return self.env.ref('homeo_doctor.action_pharmacy_report').report_action(self.original_sale_id)

    @api.onchange('original_sale_id')
    def _onchange_original_sale_id(self):
        self.return_line_ids = [(5, 0, 0)]  # Clear existing return lines
        if self.original_sale_id:
            lines = []
            for line in self.original_sale_id.prescription_line_ids:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'return_quantity': line.qty,
                    'unit_price': line.per_ped,
                    'manf_date': line.manf_date,
                    'exp_date': line.exp_date,
                    'batch': line.batch,
                    'hsn': line.hsn,
                }))
            self.return_line_ids = lines

    @api.model
    def create(self, vals):

        if not vals.get('return_number') or vals.get('return_number') == '/':

            raw_seq = self.env['ir.sequence'].next_by_code('pharmacy.return.bill') or '1'
            padded_seq = str(raw_seq).zfill(4)


            today = date.today()
            year_start = today.year % 100
            year_end = (today.year + 1) % 100
            fiscal_suffix = f"{year_start:02d}-{year_end:02d}"


            vals['return_number'] = f"{padded_seq}/{fiscal_suffix}"

        return super().create(vals)


    @api.depends('return_line_ids.subtotal')
    def _compute_return_amount(self):
        for rec in self:
            rec.total_return_amount = sum(line.subtotal for line in rec.return_line_ids)

    def action_validate_return(self):
        StockEntry = self.env['stock.entry']
        for rec in self:
            if rec.original_sale_id:
                original = rec.original_sale_id
                original.bill_amount -= rec.total_return_amount
                original.write({'bill_amount': original.bill_amount})

                # Create Stock Entry for each returned line
                for line in rec.return_line_ids:
                    if not line.product_id:
                        continue

                    # Create new stock entry for returned product
                    StockEntry.create({
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'rate': line.unit_price,
                        'manf_date': line.manf_date,
                        'exp_date': line.exp_date,
                        'batch': line.batch,
                        'hsn': line.hsn,
                        'rack': 'Returned',  # optional: mark returned rack
                        'date': fields.Date.today(),
                        'uom_id': line.product_id.uom_id.id if line.product_id.uom_id else False,
                        'state': 'confirmed',
                    })
        return self.env.ref('homeo_doctor.action_pharmacy_return_report').report_action(self)


class PharmacyReturnLine(models.Model):
    _name = 'pharmacy.return.line'
    _description = 'Pharmacy Return Line'


    product_id = fields.Many2one('product.product', string="Product")
    return_quantity = fields.Float(string="Quantity")
    quantity = fields.Float(string="Returned Quantity")
    unit_price = fields.Float(string="Unit Price")
    manf_date = fields.Date(string='M.Date')
    exp_date = fields.Date(string='Exp. Date')
    batch = fields.Char(string='Batch Number')
    hsn = fields.Char(string='HSN')
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)
    return_id = fields.Many2one('pharmacy.return', string="Return")

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id or not self.return_id.original_sale_id:
            return

        sale = self.return_id.original_sale_id
        matched_line = sale.description_line_ids.filtered(lambda l: l.product_id.id == self.product_id.id)
        if matched_line:
            line = matched_line[0]  # take the first match
            self.unit_price = line.unit_price or 0.0
            self.quantity = line.quantity or 0.0
            self.manf_date = line.manf_date
            self.exp_date = line.exp_date
            self.batch = line.batch
            self.hsn = line.hsn
        else:
            self.unit_price = 0.0
            self.quantity = 0.0
            self.manf_date = False
            self.exp_date = False
            self.batch = False
            self.hsn = False
class BillStatusWizard(models.TransientModel):
    _name = 'bill.status.wizard'
    _description = 'Bill Status Wizard'

    view_type = fields.Selection([
        ('modified', 'Modified Bills'),
        ('cancelled', 'Cancelled/Deleted Bills'),
    ], string="Bill Type", required=True)

    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")

    def fetch_bills(self):
        domain = []

        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))

        # Include both active and inactive records
        domain.append(('active', 'in', [True, False]))

        # Fetch records with context to include inactive ones
        bills = self.env['pharmacy.description'].with_context(active_test=False).search(domain)

        if self.view_type == 'modified':
            # Filter records where write_date != create_date
            bills = bills.filtered(lambda b: b.write_date and b.create_date and b.write_date != b.create_date)
        elif self.view_type == 'cancelled':
            # Filter records with status 'cancelled' or 'returned'
            bills = bills.filtered(lambda b: b.status in ['cancelled', 'returned'])

        # Clear old results so the tree view shows fresh data
        self.env['bill.status.wizard.line'].search([]).unlink()

        # Create new records to show in the tree view
        for b in bills:
            self.env['bill.status.wizard.line'].create({
                'patient_name': b.name,
                'bill_amount': b.bill_amount,
                'date': b.date,
                'status': b.status,
                'doctor_name': b.doctor_name.name if b.doctor_name else '',
                'pharmacy_description_id': b.id,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Bill Status',
            'res_model': 'bill.status.wizard.line',
            'view_mode': 'tree',
            'target': 'current',
            'context': {'active_test': False},
        }


class BillStatusWizardLine(models.TransientModel):
    _name = 'bill.status.wizard.line'
    _description = 'Bill Status Wizard Line'

    wizard_id = fields.Many2one('bill.status.wizard', string='Wizard Reference')
    patient_name = fields.Char("Patient Name")
    doctor_name = fields.Char("Doctor")
    date = fields.Datetime("Date")
    bill_amount = fields.Float("Bill Amount")
    status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string="Status")
    pharmacy_description_id = fields.Many2one('pharmacy.description', string="Pharmacy Description")

    def action_open_pharmacy_description(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pharmacy Description',
            'res_model': 'pharmacy.description',
            'view_mode': 'form',
            'res_id': self.pharmacy_description_id.id,
            'target': 'current',
        }
class BillStatus(models.Model):
    _name = 'bill.status'
    _description = 'Bill Status'




class IPReturn(models.Model):
    _name = 'ip.return'
    _description = 'IP Patient Medicine Return'
    _order = 'return_date desc'
    _rec_name='return_number'

    patient_id = fields.Many2one('patient.registration', string="UHID")
    uhid = fields.Many2one('patient.reg', string="UHID")
    uhids = fields.Many2one('pharmacy.description', string="Orginal Bill", required=True)
    patient_uhid = fields.Char(string="UHID")
    name = fields.Char(string="Patient Name", store=True)
    phone_number = fields.Char(string="Phone Number", store=True)
    original_bill_id = fields.Many2one('pharmacy.description', string="Original Bill", domain="[('op_category', '=', 'ip')]")
    return_line_ids = fields.One2many('ip.return.line', 'return_id', string="Return Lines")
    return_date = fields.Datetime(string="Return Date", default=fields.Datetime.now)
    total_return_qty = fields.Integer(string="Total Return Qty", compute='_compute_totals', store=True)
    total_return_amount = fields.Float(string="Total Return Amount", compute='_compute_totals', store=True)
    remarks = fields.Text(string="Remarks")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled')
    ], default='draft', string="Status")
    return_number = fields.Char(
        string="Return Number",
        readonly=True,
        copy=False,
        default='/',
    )

    @api.model
    def create(self, vals):

        if not vals.get('return_number') or vals.get('return_number') == '/':

            raw_seq = self.env['ir.sequence'].next_by_code('ip.return.bill') or '1'
            padded_seq = str(raw_seq).zfill(4)


            today = date.today()
            year_start = today.year % 100
            year_end = (today.year + 1) % 100
            fiscal_suffix = f"{year_start:02d}-{year_end:02d}"


            vals['return_number'] = f"{padded_seq}/{fiscal_suffix}"

        return super(IPReturn, self).create(vals)
    @api.onchange('uhids')
    def _onchange_uhids(self):
        for rec in self:
            if rec.uhids:
                rec.name = rec.uhids.name
                rec.patient_uhid = rec.uhids.uhid_id.reference_no
                rec.phone_number = rec.uhids.phone_number

    @api.depends('return_line_ids.quantity', 'return_line_ids.amount')
    def _compute_totals(self):
        for rec in self:
            rec.total_return_qty = sum(line.quantity for line in rec.return_line_ids)
            rec.total_return_amount = sum(line.amount for line in rec.return_line_ids)


    def action_validate_return(self):
        StockEntry = self.env['stock.entry']
        for rec in self:
            # Deduct return amount from the original bill if it exists
            if rec.original_bill_id:
                original = rec.original_bill_id
                original.bill_amount -= rec.total_return_amount
                original.write({'bill_amount': original.bill_amount})

            # Create Stock Entry for each returned line
            for line in rec.return_line_ids:
                if not line.medicine_id:
                    continue

                StockEntry.create({
                    'product_id': line.medicine_id.id,
                    'quantity': line.quantity,
                    'rate': line.unit_price,
                    'manf_date': line.manf_date,
                    'exp_date': line.exp_date,
                    'batch': line.batch,
                    'hsn': line.hsn,
                    'rack': 'Returned',
                    'date': fields.Date.today(),
                    'uom_id': line.medicine_id.uom_id.id if line.medicine_id.uom_id else False,
                    'state': 'confirmed',
                })
            rec.write({'state': 'returned'})


class IPReturnLine(models.Model):
    _name = 'ip.return.line'
    _description = 'IP Return Line'

    return_id = fields.Many2one('ip.return', string="Return Ref", required=True, ondelete='cascade')
    medicine_id = fields.Many2one('product.product', string="Medicine", required=True)
    manf_date = fields.Date(string='M.Date')
    exp_date = fields.Date(string='Exp. Date')
    batch = fields.Char(string='Batch Number')
    hsn = fields.Char(string='HSN')
    quantity = fields.Integer(string="Return Qty", required=True)
    unit_price = fields.Float(string="Unit Price")
    amount = fields.Float(string="Amount", compute='_compute_amount', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.unit_price


class FastMovingMedicineForm(models.TransientModel):
    _name = 'fast.moving.medicine.form'
    _description = 'Fast Moving Medicine Form'

    name = fields.Char(default='Fast Moving Report')
    from_date = fields.Date(required=True,default=fields.Date.today)
    to_date = fields.Date(required=True,default=fields.Date.today)
    line_ids = fields.One2many('fast.moving.medicine.line', 'form_id', string="Medicines")

    def compute_fast_moving(self):
        lines = self.env['pharmacy.prescription.line'].search([
            ('pharmacy_id.date', '>=', self.from_date),
            ('pharmacy_id.date', '<=', self.to_date),
        ])

        grouped = defaultdict(int)
        for l in lines:
            grouped[l.product_id.id] += l.qty or 0

        # Clear previous lines
        self.line_ids.unlink()

        # Create new lines
        for product_id, total_qty in grouped.items():
            if total_qty > 20:
                self.env['fast.moving.medicine.line'].create({
                    'form_id': self.id,
                    'product_id': product_id,
                    'total_qty': total_qty,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fast Moving Medicines',
            'res_model': 'fast.moving.medicine.form',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def print_fast_moving_report(self):
        self.ensure_one()
        self.compute_fast_moving()

        # print("Line count: %s", len(self.line_ids))  # Add logging to verify
        for line in self.line_ids:
            pass
            # print("Line: %s - %s", line.product_id.name, line.total_qty)

        return self.env.ref('homeo_doctor.action_report_fast_moving').report_action(self)


class FastMovingMedicineLine(models.TransientModel):
    _name = 'fast.moving.medicine.line'
    _description = 'Fast Moving Medicine Line'
    _order = 'total_qty desc'

    form_id = fields.Many2one('fast.moving.medicine.form', string="Form")
    product_id = fields.Many2one('product.product', string="Medicine")
    total_qty = fields.Integer(string="Total Quantity")
