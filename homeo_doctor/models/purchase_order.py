from odoo import models, fields, api

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    custom_note = fields.Char(string="Custom Note")
    supplier_id= fields.Many2one('account.move',string='Supplier No',domain="[('move_type', '=', 'in_invoice')]")
    supplier_name= fields.Char(related='supplier_id.supplier_name',string='Supplier Name')
    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        default=lambda self: self.env["res.partner"].search([], limit=1).id,
    )
