odoo.define('bill.Advanced_Search', function (require) {
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['res.partner'] = advancedSearch['res.partner'] || {};
    advancedSearch['res.partner']['bm.bill.tree'] = {
        template: 'bill.advanced_search'
    },
    advancedSearch['res.partner']['draft.bill.tree'] = {
        template: 'bill.advanced_search'
    }
    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});