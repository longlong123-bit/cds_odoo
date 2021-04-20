odoo.define('custom_module.small_dialog', function (require) {
    "use strict";
    var Dialog = require('web.Dialog');
    var timer = null;

    Dialog.include({
        willStart: function () {
            var self = this;
            window.clearTimeout(timer);
            timer = window.setTimeout(function(){
                if(self.$el && self.$el.find('.partner-table-form').length > 0){
                    self.$modal.addClass('large-modal');
                }
            }, 300);

            return this._super.apply(this, arguments);
        }
    });
});