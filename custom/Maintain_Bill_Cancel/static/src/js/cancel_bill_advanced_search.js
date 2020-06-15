odoo.define('cancel_bill.Advanced_Search', function (require) {
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['bill.info'] = advancedSearch['bill_info'] || {};
    advancedSearch['bill.info']['bm.cancel.bill.tree'] = {
        template: 'cancel_bill.advanced_search'
    }

    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});