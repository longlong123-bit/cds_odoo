odoo.define('Payment_Plan.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['bill.info'] = advancedSearch['bill.info'] || {};
    advancedSearch['bill.info']['payment.plan.tree.view'] = {
        template: 'payment_plan.advanced_search'
    }
    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});
