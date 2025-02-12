odoo.define('homeo_doctor.title', function (require) {
    "use strict";

    var WebClient = require('web.WebClient');

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
});