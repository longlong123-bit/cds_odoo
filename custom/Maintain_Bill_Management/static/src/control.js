odoo.define('bm.web_view', function(require){
    "use strict";

    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require("web.ListController");

    var includeDict = {
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName === "company.office.custom") {
                var treeButton = this.$buttons.find('button.o_button_billtree')
                treeButton.on('click', this.proxy('o_button_help'))
            }
        },

        o_button_help: function(){
            var self = this;
            this.rpc.query({
                model: 'bm.bill',
                method: 'redirect_to_tree',
                args: [{}]
            }, {
                shadow: true,
            }).then(function (res) {
                return self.do_action(res);
            });
        }
    };

    ListController.include(includeDict);
});
