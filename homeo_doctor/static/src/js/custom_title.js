odoo.define('homeo_doctor.title', function (require) {
    "use strict";

    var WebClient = require('web.WebClient');

    var FormController = require('web.FormController');
    var session = require('web.session');

    WebClient.include({
        set_title_part: function (part, title) {
            var parts = this.get('title_part');
            parts = _.extend({}, parts);
            if (title === undefined) {
                delete parts[part];
            } else {
                parts[part] = title;
            }
            parts['zopenerp'] = false;  // This removes "Odoo" from the title
            this.set('title_part', parts);
            return this._super.apply(this, arguments);
        },

        _title_changed: function () {
            var parts = _.sortBy(_.keys(this.get('title_part')));
            var title = '';
            _.each(parts, function(part) {
                var str = this.get('title_part')[part];
                if (str && part !== 'zopenerp') {  // Skip the Odoo part
                    title = str;
                }
            }.bind(this));
            document.title = title || '';  // Set title to form/menu name only
        }
    });
    const RESTRICTED_MODELS = [
        'stock.transfer',
        'doctor.lab.report',
        'general.billing',
        'ip.part.billing',
        'ip.insurance.billing',

    ];

    FormController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);

            if (!this.$buttons || !this.modelName) {
                return;
            }

            // Apply only to selected models
            if (!RESTRICTED_MODELS.includes(this.modelName)) {
                return;
            }

            Promise.all([
                session.user_has_group('base.group_system'), // Admin
                session.user_has_group('homeo_doctor.group_allowed_edit'), // Allowed users
            ]).then((results) => {
                const isAdmin = results[0];
                const hasAllowedGroup = results[1];

                // Hide Edit button if NOT admin and NOT allowed group
                if (!isAdmin && !hasAllowedGroup) {
                    this.$buttons.find('.o_form_button_edit').hide();
                }
            });
        },
    });
});