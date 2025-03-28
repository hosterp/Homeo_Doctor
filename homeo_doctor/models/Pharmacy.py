from odoo import api, fields, models


class PharmacyDescription(models.Model):
    _name = 'pharmacy.description'
    _description = 'Pharmacy Description'
    _order = 'date desc'
    patient_id = fields.Many2one('patient.registration',string="Patient ID")
    _order = 'date desc'
    patient_id = fields.Many2one('patient.registration',string="UHID")
    name = fields.Char(string="Patient Name")
    phone_number = fields.Char(string="Phone Number")
    # bill_amount=fields.Integer(string='Bill Amount')
    doctor_name=fields.Char(string='Doctor')
    date= fields.Datetime(string="Date",default=fields.Datetime.now)
    prescription_line_ids = fields.One2many('pharmacy.prescription.line', 'pharmacy_id', string="Prescriptions")
    bill_amount = fields.Float(string="Total Bill Amount", compute="_compute_bill_amount", store=True)
    partner_id = fields.Many2one('res.partner', string="Related Partner")

    @api.model
    def create(self, vals):
        # When creating a patient, also create or find a partner
        res = super(PharmacyDescription, self).create(vals)
        if not res.partner_id and res.name:
            partner = self.env['res.partner'].search([
                ('name', '=', res.name),
                # Add other fields to match if needed
            ], limit=1)

            if not partner:
                partner = self.env['res.partner'].create({
                    'name': res.name,
                    # Add other values as needed
                })

            res.partner_id = partner.id
        return res


    @api.depends('prescription_line_ids.rate', 'prescription_line_ids.gst')
    def _compute_bill_amount(self):
        for rec in self:
            rec.bill_amount = sum(line.rate for line in rec.prescription_line_ids)  # Excluding GST

    def action_register_payment(self):
    # First, ensure there's a partner_id for this patient
        partner = False
        if self.patient_id and hasattr(self.patient_id, 'partner_id') and self.patient_id.partner_id:
            partner = self.patient_id.partner_id.id
        else:
            # Look for existing partner with same name/phone
            partner = self.env['res.partner'].search([
                ('name', '=', self.name),
                ('phone', '=', self.phone_number)
            ], limit=1)

            if not partner:
                # Create a new partner for this patient
                partner = self.env['res.partner'].create({
                    'name': self.name,
                    'phone': self.phone_number,
                }).id
            else:
                partner = partner.id

        return {
        'name': 'Register Payment',
        'type': 'ir.actions.act_window',
        'res_model': 'account.payment',
        'view_mode': 'form',
        'view_id': self.env.ref('homeo_doctor.view_account_payment_form_inherit').id,
        'target': 'new',
        'context': {
            'default_pharm_id': self.id,
            'default_amount': self.bill_amount,
            'default_payment_type': 'inbound',
            'default_communication': self.name,  # This is fine, communication isn't used for sequence
            'default_payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'default_journal_id': self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id,
            # Remove the next line to let Odoo handle the sequence
            'default_name': self.name,
            'default_uhid': self.patient_id.id if self.patient_id else False,
            'default_partner_id': partner,
            'default_partner_type': 'customer',
        }
    }

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
                if entry.quantity >= remaining_qty:
                    entry.quantity -= remaining_qty
                    remaining_qty = 0
                else:
                    remaining_qty -= entry.quantity
                    entry.quantity = 0

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
                rec.rate = rec.per_ped * rec.qty
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
