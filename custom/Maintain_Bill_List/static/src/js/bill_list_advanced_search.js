odoo.define('bill_list.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['bill.info'] = advancedSearch['bill.info'] || {};
    advancedSearch['bill.info']['bm.bill.list.tree.in.bill.management'] = {
        template: 'bill_list.advanced_search'
    }

    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});