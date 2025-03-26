from odoo import models, fields, api

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    custom_note = fields.Char(string="Custom Note")
    supplier_id= fields.Many2one('account.move',string='Supplier No',domain="[('move_type', '=', 'in_invoice')]")
    supplier_name= fields.Many2one('supplier.name',string='Supplier Name')
    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        default=lambda self: self.env["res.partner"].search([], limit=1).id,
    )
    store_in_charge=fields.Many2one('store.incharge',string='Store in charge')
    approved_by=fields.Many2one('approved.store.person',string='Approved By')
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('approved', 'Approved'),  # Add the new state
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ]
    state = fields.Selection(STATE_SELECTION, string='Status', default='draft')

    def action_create_invoice(self):
        super(PurchaseOrderInherit, self).action_create_invoice()  

        for order in self:
            if order.invoice_ids:
                invoice = order.invoice_ids[0]

                # Update invoice fields
                invoice.write({
                    'supplier_name': order.supplier_name.display_name,
                    'po_number': order.id,
                })


                if invoice.state == 'draft':
                    invoice.action_post()

        return True
class ApprovedPerson(models.Model):
    _name='approved.store.person'
    _rec_name='approved_by'

    approved_by=fields.Char(string='Approved By')


class StoreInCharge(models.Model):
    _name='store.incharge'
    _rec_name='store_incharge'


    store_incharge= fields.Char(string='Store In Charge')


class PurchaseOrderLine(models.Model):
    _inherit='purchase.order.line'

    company=fields.Char(string='Company')

class SupplierCreation(models.Model):
    _name = 'supplier.name'
    _rec_name = 'supplier'

    supplier=fields.Char('Supplier')