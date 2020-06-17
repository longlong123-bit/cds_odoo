odoo.define('Payment_Request_Bill.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['bill.info'] = advancedSearch['bill.info'] || {};
    advancedSearch['bill.info']['payment.request.tree.view'] = {
        template: 'payment_request_bill.advanced_search'
    }
    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});
