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
                              )
    experience_years = fields.Integer(string='Years of Experience')
    available_days = fields.Selection([('monday', 'Monday'), ('tuesday', 'Tuesday'),('wednesday', 'Wednesday'),('thursday', 'Thursday'),('friday', 'Friday'),('saturday', 'Saturday'),('sunday', 'Sunday')], string='Available Days')
    available_hours = fields.Char(string='Available Hours')
    bio = fields.Text(string='Doctor Bio')

    @api.model
    def create(self, vals):
        if vals.get('doctor_id', 'New') == 'New':

            user_id = vals.get('user_id')
            if user_id:
                vals['doctor_id'] = f"DOCTOR-{user_id}"
            else:
                vals['doctor_id'] = self.env['ir.sequence'].next_by_code('doctor.profile') or 'New'
        return super(DoctorProfile, self).create(vals)