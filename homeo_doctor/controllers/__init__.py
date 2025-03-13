from . import main

import requests
from odoo import http
from odoo.http import request

class AuthLogin(http.Controller):
    @http.route('/web/login', type='http', auth="public", website=True)
    def web_login(self, redirect=None, **kw):
        recaptcha_response = kw.get('g-recaptcha-response')
        secret_key = ""

        # Verify reCAPTCHA
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={'secret': secret_key, 'response': recaptcha_response}
        ).json()

        if not response.get("success"):
            return request.render('web.login', {'error': 'Invalid reCAPTCHA. Try again.'})

        return http.redirect_with_hash('/web')
