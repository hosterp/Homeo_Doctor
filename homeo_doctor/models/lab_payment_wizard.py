from odoo import api, fields, models, _


class LabPaymentWizard(models.Model):
    _name = 'lab.payment'



    patient_id=fields.Many2one('doctor.lab.report',string='Patient ID')
    patient_name=fields.Char(related='patient_id.patient_name',string='Patient Name')
    pay_mode = fields.Selection([('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'),('credit','Credit')], string='Payment Method',
                                default='cash')
    total_amount=fields.Integer(string='Payable Amount')
    amount_paid=fields.Integer(string='Amount Paid')
    balance=fields.Integer(string='Balance')

    @api.onchange('amount_paid')
    def _onchage_amount_paid(self):
        for rec in self:
            if (rec.amount_paid < rec.total_amount and rec.amount_paid > 0):
                rec.balance = rec.total_amount - rec.amount_paid
            elif(rec.amount_paid > rec.total_amount and rec.amount_paid >    0):
                rec.balance = rec.amount_paid -  rec.total_amount


    def action_confirm_payment(self):
        # Get the related doctor.lab.report record
        lab_report = self.patient_id
        
        # Update the status to 'paid'
        if lab_report:
            lab_report.write({
                'status': 'paid'
            })
        
        # Close the wizard
        return {'type': 'ir.actions.act_window_close'}


