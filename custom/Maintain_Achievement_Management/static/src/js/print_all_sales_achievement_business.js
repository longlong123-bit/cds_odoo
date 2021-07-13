odoo.define('sales.print_all_sales_achievement_business', function (require) {
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

            if (context['model'] !== undefined) {
                var model = context['model'];
            }
            if (context['sales_achievement_business'] === undefined || context['view_name'] !== 'sales_achievement_business') {
                this.$buttons && this.$buttons.find('button.print_all_sales_achievement_business') && this.$buttons.find('button.print_all_sales_achievement_business').hide();
            } else {
                this.$buttons.on('click', '.print_all_sales_achievement_business', function (e) {
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
                        method: 'print_all_sales_achievement_business',
                        args: ['', selected_data, self.getSelectedIds()],
                        data: {
                            context: JSON.stringify(session.user_context),
                        }
                    }, {
                        timeout: 6000000,
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
