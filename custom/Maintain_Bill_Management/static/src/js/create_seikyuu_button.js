odoo.define('seikyuu.create_seikyuu_button', function (require) {
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
            if (context['seikyuu_module'] === undefined) {
                this.$buttons.find('button.btn_test').hide();
            } else {
                this.$buttons.find('button.o_list_button_add').hide();
                this.$buttons.find('button.o_button_import').hide();
                this.$buttons.find('button.o_list_button_save').hide();
                this.$buttons.find('button.o_list_button_discard').hide();
                this.$buttons.on('click', '.btn_test', function (e) {
                    // debugger;
                    var def = new $.Deferred();
                    console.log(model)
                    // rpc.query({
                    //     model: model,
                    //     method: 'btn_test',
                    //     args: [self.model.data.context.active_ids[0]],
                    //     data: {
                    //         context: JSON.stringify(session.user_context),
                    //     },
                    // }, {
                    //     timeout: 3000,
                    //     shadow: true,
                    // })
                    //     .then(function (result) {
                    //         return self.do_action(result);
                    //     }, function (type, err) {
                    //         def.reject();
                    //     });
                    // return def;
                    return true;
                });
            }
        }
    };
    
    ListController.include(includeDict);
});
