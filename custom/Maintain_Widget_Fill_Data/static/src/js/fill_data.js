odoo.define('fill_data', function(require){
    var core = require('web.core');
    var formView = require('web.FormView');

    var MyWidget = formView.include({
        init: function (parent, model, state) {
            this._super(parent);
            // init code here
        },
        start: function () {
             //codes
        },
        events: _.extend({}, formView.prototype.events, {
            "click button.fill_data": "_openSearchDialog",
        }),
        _openSearchDialog: function (e) {
            //codes...
            console.log(e);
        },
        display_filter: function () {
            //codes...
        },
    });
});