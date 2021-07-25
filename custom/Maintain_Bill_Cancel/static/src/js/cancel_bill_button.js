odoo.define('bill.cancel_bill_button', function (require) {
    "use strict";
    var framework = require('web.framework');
    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var core = require('web.core');
    var _t = core._t;
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
            if (context['bill_management_module'] === undefined || context['view_name'] !== 'Cancel Billing') {
                this.$buttons && this.$buttons.find('button.cancel_bill_button') && this.$buttons.find('button.cancel_bill_button').hide();
            } else {
                this.$buttons.on('click', '.cancel_bill_for_invoice', function (e) {
                    framework.blockUI();
                    const def = new $.Deferred();
                    var selected_data = [];
                    data = window.current_data || data;
                    if (data) {
                        for (var i = 0; i < data.length; i++) {
                            if (self.getSelectedIds().includes(data[i].res_id)) {
                                selected_data.push(data[i].data)
                            }
                        }
                    }

                    if (selected_data.length == 0) {
                        framework.unblockUI();
                        return def;
                    }

                    rpc.query({
                        model: model,
                        method: 'cancel_bill_for_invoice',
                        args: ['', selected_data, self.getSelectedIds()],
                        data: {
                            context: JSON.stringify(session.user_context),
                        }
                    }, {
                        timeout: 6000000,
                        shadow: true
                    }).then(function (result) {
                        if (result) {
                            framework.unblockUI();
                            self.do_notify('Infomation','請求処理の取消が完了しました。',false);
                            return self.do_action(result)
                        }else{
                            framework.unblockUI();
                            self.do_warn('エラー',"最新締切がある請求処理のみを取消できます。",false);
                        }
                    })
                    return def;
                });
            }
        },
    }
    ListController.include(includeDict);
});
