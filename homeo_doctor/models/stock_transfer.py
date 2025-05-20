from datetime import date

from odoo import models, fields,api,_
from odoo.exceptions import ValidationError, UserError


class StockTransfer(models.Model):
    _name = 'stock.transfer'
    _description = 'Stock Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", required=True, copy=False, default=lambda self: _('New'))
    date = fields.Date(string='Date', default=fields.Date.context_today)
    location_from = fields.Char(string='From Location')
    location_to = fields.Char(string='To Location')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string="Status", default="draft", tracking=True)

    # One2many relationship with StockTransferLine
    line_ids = fields.One2many('stock.transfer.line', 'transfer_id', string='Transfer Lines')

    # Sequence generation
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer') or _('New')
        return super(StockTransfer, self).create(vals)

    # State transition buttons
    def action_confirm(self):
        self.state = 'confirmed'

    def action_done(self):
        for record in self:
            for line in record.line_ids:
                # Update stock.entry based on transfer type (add/remove)
                if line.is_addition:
                    # Logic to add stock
                    self._add_to_stock(line)
                else:
                    # Logic to remove stock
                    self._remove_from_stock(line)
        self.state = 'done'

    def _add_to_stock(self, line):
        """Add product to stock"""
        self.env['stock.entry'].create({
            'name': self.env['ir.sequence'].next_by_code('stock.entry') or _('New'),
            'product_id': line.product_id.id,
            'quantity': line.quantity,
            'rate': line.rate,
            'uom_id': line.uom_id.id,
            'date': self.date,
            'manf_date': line.manf_date,
            'exp_date': line.exp_date,
            'hsn': line.hsn,
            'rack': line.rack,
            'batch': line.batch,
            'pack': line.pack,
            'state': 'confirmed',
        })

    def _remove_from_stock(self, line):
        """Remove product from stock - you'll need to implement the logic
        based on your specific requirements and stock handling approach"""
        # Find matching stock entries
        stock_entries = self.env['stock.entry'].search([
            ('product_id', '=', line.product_id.id),
            ('state', '=', 'confirmed'),
        ], order='date')

        remaining_qty = line.quantity
        for entry in stock_entries:
            if remaining_qty <= 0:
                break

            if entry.quantity > remaining_qty:
                entry.quantity -= remaining_qty
                remaining_qty = 0
            else:
                remaining_qty -= entry.quantity
                entry.quantity = 0
                entry.state = 'done'  # Mark as fully consumed

        if remaining_qty > 0:
            # Not enough stock found
            raise UserError(_('Not enough stock available for %s. Short by %s units.') %
                            (line.product_id.name, remaining_qty))


class StockTransferLine(models.Model):
    _name = 'stock.transfer.line'
    _description = 'Stock Transfer Line'

    transfer_id = fields.Many2one('stock.transfer', string='Transfer Reference')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    is_addition = fields.Boolean(string="Add to Stock", help="Check if adding to stock, uncheck if removing")
    quantity = fields.Float(string="Quantity", required=True)
    rate = fields.Float(string="Rate", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    manf_date = fields.Date(string='M.Date')
    hsn = fields.Char(string='HSN')
    exp_date = fields.Date(string='Exp.date')
    rack = fields.Char(string='Rack Position')
    batch = fields.Char(string='Batch Number')
    pack = fields.Integer(string="Pack", default=1)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
            # You might want to fetch the last rate or other details here
            last_entry = self.env['stock.entry'].search([
                ('product_id', '=', self.product_id.id),
                ('state', '=', 'confirmed')
            ], order='create_date desc', limit=1)

            if last_entry:
                self.rate = last_entry.rate
                self.hsn = last_entry.hsn