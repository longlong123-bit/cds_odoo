odoo.define('seikyuu.menu.tree', function (require) {
    "use strict";

    var ListController = require("web.ListController");
    var includeDict = {
        renderButtons: function () {

            var self = this;
            var data = this.model.get(this.handle);
            this._super.apply(this, arguments);
            self.$buttons.on('click', '.btn_test',function () {
                self._rpc({
                    route: '/web/action/load',
                    params: {
                        action_id: 'base.actions_bm_seikyuu_details',
                    },
                })
                    .then(function (r) {
                        console.log(r);
                        return self.do_action(r);
                    });
            });
        }
    };

    ListController.include(includeDict);
});