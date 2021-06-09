odoo.define('bill.print_all_bill_button', function (require) {
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
            var data = this.model.get(this.handle).data;

            if (context['model'] !== undefined
            ) {
                var model = context['model'];
            }
            if (context['bill_management_module'] === undefined || context['view_name'] !== 'Payment Request Billing') {
                this.$buttons && this.$buttons.find('button.print_all_bill_button') && this.$buttons.find('button.print_all_bill_button').hide();
            } else {
                this.$buttons.on('click', '.print_all_bill_button', function (e) {
                    const def = new $.Deferred();
                    var selected_data = [];
//                    data = window.current_data || data;
//                    if (data) {
//                        for (var i = 0; i < data.length; i++) {
//                            if (self.getSelectedIds().includes(data[i].res_id)) {
//                                selected_data.push(data[i].data)
//                            }
//                        }
//                    }
                    rpc.query({
                        model: model,
                        method: 'print_all_bill_button',
                        args: ['', selected_data, self.getSelectedIds()],
                        data: {
                            context: JSON.stringify(session.user_context),
                        }
                    }, {
                        timeout: 300000,
                        shadow: true
                    }).then(function (result) {
                        if (result) {
                            return self.do_action(result)
                        }
                    })
                    return def;
                });
            }
        },
    }
    ListController.include(includeDict);
});
