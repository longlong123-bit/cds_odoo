odoo.define('bill.create_bill_button', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var FormController = require('web.FormController');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var includeDict = {
        renderButtons: function () {
            var self = this;
            var model = this.modelName;
            this._super.apply(this, arguments);
            var context = this.model.get(this.handle).context;
            var data = this.model.get(this.handle).data;
            if (context['model'] !== undefined) {
                var model = context['model'];
            }
            if (context['bill_management_module'] === undefined) {
                this.$buttons && this.$buttons.find('button.create_bill_button') && this.$buttons.find('button.create_bill_button').hide();
            }
            else {
                this.$buttons.find('button.o_list_button_add').hide();
                this.$buttons.find('button.o_button_import').hide();
                this.$buttons.find('button.o_list_button_save').hide();
                this.$buttons.find('button.o_list_button_discard').hide();
                this.$buttons.find('button.o_form_button_save').hide();
                this.$buttons.find('button.o_form_button_cancel').hide();

                this.$buttons.on('click', '.create_bill_button', function (e) {
                    const def = new $.Deferred();
                    var selected_data = [];
                    data = window.current_data || data;
                    if (data) {
                        for (var i = 0; i < data.length; i++) {
                            if (self.getSelectedIds().includes(data[i].res_id)) {
                                selected_data.push(data[i].data);
                            }
                        }
                    }
                    rpc.query({
                        model: model,
                        method: 'create_bill_for_invoice',
                        args: ['', selected_data],
                        data: {
                            context: JSON.stringify(session.user_context),
                        }
                    }, {
                        timeout: 3000,
                        shadow: true
                    }).then(function (result) {
                        return self.do_action(result)
                    })
                    return def;
                });
            }
        },
    }
    ListController.include(includeDict);
    FormController.include(includeDict);
});
