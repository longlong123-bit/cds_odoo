odoo.define('bill.create_bill_button', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var includeDict = {
        renderButtons: function () {
            var self = this;
            var model = this.modelName;
            this._super.apply(this, arguments);
            var context = this.model.get(this.handle).context;
            if (context['model'] !== undefined) {
                var model = context['model'];
            }
            if (context['bill_management_module'] === undefined) {
                this.$buttons.find('button.create_bill_button').hide();
            } else {
                this.$buttons.find('button.o_list_button_add').hide();
                this.$buttons.find('button.o_button_import').hide();
                this.$buttons.find('button.o_list_button_save').hide();
                this.$buttons.find('button.o_list_button_discard').hide();

                this.$buttons.on('click', '.create_bill_button', function (e) {
                    const def = new $.Deferred();
                    console.log("model => ", model);
                    rpc.query({
                        model: model,
                        method: 'create_bill_for_invoice',
                        args: ['', model],
                        data: {
                            context: JSON.stringify(session.user_context),
                        }
                    }, {
                        timeout: 3000,
                        shadow: true
                    })
                    return def;
                });
            }
        },
    }
    ListController.include(includeDict);
});
