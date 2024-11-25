from odoo import api, fields, models

class DoctorProfile(models.Model):
    _name = 'doctor.profile'
    _description = 'Doctor Profile'
    _rec_name = 'name'


    name = fields.Char(string='Doctor Name', required=True)
    specialization = fields.Char(string='Specialization')
    phone = fields.Char(string='Phone Number', required=True)
    email = fields.Char(string='Email')
    qualification = fields.Char(string='Qualification')
    joining_date = fields.Date(string='Joining Date', default=fields.Date.context_today)
    doctor_id = fields.Char(string="Doctor ID", readonly=True, copy=False, default="New")
    user_id = fields.Many2one('res.users', string="Assigned User", ondelete='cascade',
                              required=True)  # user_id as primary key

    @api.model
    def create(self, vals):
        if vals.get('doctor_id', 'New') == 'New':
            # Generate a doctor ID based on the user_id or any other logic
            user_id = vals.get('user_id')
            if user_id:
                vals['doctor_id'] = f"DOCTOR-{user_id}"  # Example: doctor_id based on user_id
            else:
                vals['doctor_id'] = self.env['ir.sequence'].next_by_code('doctor.profile') or 'New'
        return super(DoctorProfile, self).create(vals)