odoo.define('cancel_bill.Advanced_Search', function (require) {
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'bill.info': {
                'bm.cancel.bill.tree': {
                    template: 'cancel_bill.advanced_search'
                }
            }
        })
    });
});