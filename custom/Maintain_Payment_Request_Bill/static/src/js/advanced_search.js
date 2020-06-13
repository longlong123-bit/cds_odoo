odoo.define('Payment_Request_Bill.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'bill.info': {
                'payment.request.tree.view':{
                    template: 'payment_request_bill.advanced_search'
                }
            }
        })
    });
});
