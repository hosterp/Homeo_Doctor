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
    store_in_charge=fields.Many2one('store.incharge',string='Store in charge')
    approved_by=fields.Many2one('approved.store.person',string='Approved By')


class ApprovedPerson(models.Model):
    _name='approved.store.person'
    _rec_name='approved_by'

    approved_by=fields.Char(string='Approved By')


class StoreInCharge(models.Model):
    _name='store.incharge'
    _rec_name='store_incharge'


    store_incharge= fields.Char(string='Store In Charge')